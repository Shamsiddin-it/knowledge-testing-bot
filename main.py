import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db import Base, User, Test, Question, CorrectAnswer, UserAnswer, engine, async_session
from config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/add_test')], [KeyboardButton(text='/pass_test')], [KeyboardButton(text='/my_stats')], [KeyboardButton(text='/cancel')]],
    resize_keyboard=True, one_time_keyboard=False
)

class MyStates(StatesGroup):
    title_test = State()
    questions = State()
    title_question = State()
    v1 = State()
    v2 = State()
    v3 = State()
    v4 = State()
    correct_answer = State()

    choosing_test = State()
    answering = State()

@dp.message(F.text == '/start')
async def start(message: Message):
    await message.answer("Welcome to our testing knowledge bot!", reply_markup=kb)
    async with async_session() as session:
        user = User(username=message.from_user.username, tg_id=message.from_user.id)
        users = await select(User).where(User.tg_id==message.from_user.id)
        if user not in users:
            session.add(user)
            await session.commit()


@dp.message(F.text == '/cancel')
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Operation cancelled.", reply_markup=kb)


@dp.message(F.text == '/add_test')
async def add_test(message: Message, state: FSMContext):
    await message.answer("Enter title of test:")
    await state.set_state(MyStates.title_test)

@dp.message(MyStates.title_test)
async def enter_test_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Enter number of questions:")
    await state.set_state(MyStates.questions)

@dp.message(MyStates.questions)
async def enter_question_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer("Please enter a valid number.")
        return

    await state.update_data(questions=count, cnt=1)

    data = await state.get_data()
    async with async_session() as session:
        test = Test(title=data['title'], questions=count)
        session.add(test)
        await session.commit()

    await message.answer("Enter title of question №1:")
    await state.set_state(MyStates.title_question)

@dp.message(MyStates.title_question)
async def enter_question_title(message: Message, state: FSMContext):
    await state.update_data(question_title=message.text)
    await message.answer("Enter variant A:")
    await state.set_state(MyStates.v1)

@dp.message(MyStates.v1)
async def enter_v1(message: Message, state: FSMContext):
    await state.update_data(v1=message.text)
    await message.answer("Enter variant B:")
    await state.set_state(MyStates.v2)

@dp.message(MyStates.v2)
async def enter_v2(message: Message, state: FSMContext):
    await state.update_data(v2=message.text)
    await message.answer("Enter variant C:")
    await state.set_state(MyStates.v3)

@dp.message(MyStates.v3)
async def enter_v3(message: Message, state: FSMContext):
    await state.update_data(v3=message.text)
    await message.answer("Enter variant D:")
    await state.set_state(MyStates.v4)

@dp.message(MyStates.v4)
async def enter_v4(message: Message, state: FSMContext):
    await state.update_data(v4=message.text)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A", callback_data="correct_A"), InlineKeyboardButton(text="B", callback_data="correct_B")],
        [InlineKeyboardButton(text="C", callback_data="correct_C"), InlineKeyboardButton(text="D", callback_data="correct_D")]
    ])
    await message.answer("Select the correct answer:", reply_markup=markup)
    await state.set_state(MyStates.correct_answer)

@dp.callback_query(MyStates.correct_answer)
async def save_question(callback: CallbackQuery, state: FSMContext):
    correct = callback.data.split("_")[1]
    data = await state.get_data()

    async with async_session() as session:
        test = (await session.execute(select(Test).where(Test.title == data['title']))).scalar_one()
        question = Question(
            title=data['question_title'],
            variant_A=data['v1'], variant_B=data['v2'],
            variant_C=data['v3'], variant_D=data['v4'],
            test_id=test.id
        )
        session.add(question)
        await session.commit()

        correct_answer = CorrectAnswer(question_id=question.id, correct_option=correct)
        session.add(correct_answer)
        await session.commit()

    if data['cnt'] < data['questions']:
        await state.update_data(cnt=data['cnt'] + 1)
        await callback.message.answer(f"Enter title of question №{data['cnt'] + 1}:")
        await state.set_state(MyStates.title_question)
    else:
        await callback.message.answer("Test added successfully!")
        await state.clear()

@dp.message(F.text == '/pass_test')
async def choose_test(message: Message, state: FSMContext):
    async with async_session() as session:
        tests = (await session.execute(select(Test))).scalars().all()

    if not tests:
        await message.answer("No tests available.")
        return
    
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for test in tests:
        markup.inline_keyboard.append([InlineKeyboardButton(text=test.title, callback_data=f"starttest_{test.id}")])

    await message.answer("Choose a test to pass:", reply_markup=markup)
    await state.set_state(MyStates.choosing_test)

@dp.callback_query(F.data.startswith("starttest_"))
async def start_test(callback: CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        questions = (await session.execute(select(Question).where(Question.test_id == test_id))).scalars().all()

    if not questions:
        await callback.message.answer("No questions in this test.")
        return

    await state.update_data(test_id=test_id, questions=[q.id for q in questions], current=0, correct=0)
    await send_next_question(callback.message, state)

async def send_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data['current']
    questions = data['questions']

    if current >= len(questions):
        await message.answer(f"Test completed!\nCorrect answers: {data['correct']}/{len(questions)}")
        await state.clear()
        return

    question_id = questions[current]
    async with async_session() as session:
        question = await session.get(Question, question_id)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=question.variant_A, callback_data="A")],
        [InlineKeyboardButton(text=question.variant_B, callback_data="B")],
        [InlineKeyboardButton(text=question.variant_C, callback_data="C")],
        [InlineKeyboardButton(text=question.variant_D, callback_data="D")],
    ])
    await message.answer(f"{current + 1}. {question.title}", reply_markup=markup)
    await state.set_state(MyStates.answering)

@dp.callback_query(MyStates.answering)
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    selected = callback.data
    data = await state.get_data()
    current = data['current']
    question_id = data['questions'][current]

    async with async_session() as session:
        correct = (await session.execute(select(CorrectAnswer).where(CorrectAnswer.question_id == question_id))).scalar_one()
        user = (await session.execute(select(User).where(User.tg_id == callback.from_user.id))).scalars().all()[0]
        is_correct = correct.correct_option == selected

        if user:
            ua = UserAnswer(
                user_id=user.id,
                question_id=question_id,
                selected_answer=selected,
                is_correct=is_correct
            )
            session.add(ua)
            await session.commit()

    if is_correct:
        data['correct'] += 1
    data['current'] += 1
    await state.update_data(data)
    await send_next_question(callback.message, state)

@dp.message(F.text == '/my_stats')
async def show_stats(message: Message):
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.tg_id == message.from_user.id))).scalars().all()[0]

        if not user:
            await message.answer("User not found.")
            return

        answers = (await session.execute(select(UserAnswer).where(UserAnswer.user_id == user.id))).scalars().all()

        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)

        await message.answer(f"Your stats:\nTotal answers: {total}\n Correct: {correct}\n Wrong: {total - correct}")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
