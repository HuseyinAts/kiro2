import asyncio
import logging
from datetime import datetime, timezone
import re
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session_context
from models.user_models import User
from models.question_bank import QuestionBankItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def purge_toxic_users(session: AsyncSession):
    # L6: Dummy data ("test", "asdf")
    logger.info("Soft-deleting toxic/dummy user data (L6)...")
    toxic_patterns = ['test%', '%asdf%']
    deleted_count = 0
    for pattern in toxic_patterns:
        stmt = update(User).where(User.username.ilike(pattern) | User.email.ilike(pattern)).values(is_active=False)
        result = await session.execute(stmt)
        deleted_count += result.rowcount
    
    # L14: Invalid password hashes (less than 30 chars, usually bcrypt is 60)
    logger.info("Soft-deleting invalid password hashes (L14)...")
    stmt2 = update(User).where(func.length(User.password_hash) < 30).values(is_active=False)
    result2 = await session.execute(stmt2)
    deleted_count += result2.rowcount
    
    # L9: Future-dated users
    logger.info("Soft-deleting future-dated users (L9)...")
    now_utc = datetime.now(timezone.utc)
    stmt3 = update(User).where(User.created_at > now_utc).values(is_active=False)
    result3 = await session.execute(stmt3)
    deleted_count += result3.rowcount
    
    logger.info(f"Total soft-deleted users: {deleted_count}")

async def clean_questions(session: AsyncSession):
    # L8: Semantic Plausibility (option_a == option_b)
    logger.info("Deactivating questions with identical options (L8)...")
    stmt = update(QuestionBankItem).where(
        QuestionBankItem.option_a == QuestionBankItem.option_b
    ).values(is_active=False)
    result = await session.execute(stmt)
    logger.info(f"Deactivated {result.rowcount} questions with identical options.")

    # L2: HTML leaks in question text
    logger.info("Cleaning HTML leaks from question text (L2)...")
    # Fetch all questions containing '<div', '<html', 'href='
    q_stmt = select(QuestionBankItem).where(
        QuestionBankItem.question_text.ilike('%<div%') |
        QuestionBankItem.question_text.ilike('%<html%') |
        QuestionBankItem.question_text.ilike('%href=%')
    )
    result_q = await session.execute(q_stmt)
    questions = result_q.scalars().all()
    cleaned = 0
    for q in questions:
        # Simple regex to strip HTML tags
        if q.question_text:
            clean_text = re.sub(r'<[^>]+>', '', q.question_text)
            q.question_text = clean_text
            cleaned += 1
    logger.info(f"Cleaned HTML tags from {cleaned} questions.")

    # L10: Broken LaTeX (missing $ for \sum)
    logger.info("Fixing broken LaTeX (L10)...")
    latex_stmt = select(QuestionBankItem).where(
        QuestionBankItem.question_text.like('%\\sum%') &
        ~QuestionBankItem.question_text.like('%$%')
    )
    result_latex = await session.execute(latex_stmt)
    latex_questions = result_latex.scalars().all()
    fixed_latex = 0
    for q in latex_questions:
        if q.question_text:
            # Wrap \sum expression in $ (simplified patch)
            q.question_text = q.question_text.replace(r'\sum', r'$\sum$')
            fixed_latex += 1
    logger.info(f"Fixed LaTeX in {fixed_latex} questions.")

async def main():
    async with get_db_session_context() as session:
        await purge_toxic_users(session)
        await clean_questions(session)
        await session.commit()
        logger.info("Data purging and cleansing complete.")

if __name__ == "__main__":
    asyncio.run(main())
