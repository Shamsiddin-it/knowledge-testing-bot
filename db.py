from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, ForeignKey
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    tg_id = Column(BigInteger)
    full_name = Column(String)
    phone = Column(String)

class Test(Base):
    __tablename__ = 'tests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    questions = Column(Integer)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    variant_A = Column(String)
    variant_B = Column(String)
    variant_C = Column(String)
    variant_D = Column(String)
    test_id = Column(Integer, ForeignKey(Test.id))

class CorrectAnswer(Base):
    __tablename__ = 'correct_answers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey(Question.id))
    correct_option = Column(String)  # A, B, C, D

class UserAnswer(Base):
    __tablename__ = 'user_answers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    question_id = Column(Integer, ForeignKey(Question.id))
    selected_answer = Column(String)
    is_correct = Column(Boolean)