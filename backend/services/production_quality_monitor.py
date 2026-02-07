"""
Production Quality Monitor - Track enhanced template performance in real-time

This service monitors all questions generated in production and tracks:
- Wave 2B quality scores
- Approval rates
- Subject-specific performance
- Length and Bloom level distribution

Usage:
    from services.production_quality_monitor import ProductionQualityMonitor

    monitor = ProductionQualityMonitor()
    await monitor.log_question(question, evaluation)
    report = await monitor.generate_report()
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import statistics

from services.comprehensive_quality_evaluator import ComprehensiveQualityEvaluator
from database.connection import async_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class QuestionLog:
    """Log entry for a generated question"""

    timestamp: str
    subject: str
    topic: str
    question_id: str
    length: int
    wave2b_score: float
    decision: str
    bloom_level: int
    enhanced: bool  # Whether enhanced template was used


class ProductionQualityMonitor:
    """Monitor question quality in production"""

    def __init__(self, log_file: str = "production_quality_log.json"):
        self.log_file = Path(__file__).parent.parent / log_file
        self.logs: List[QuestionLog] = []
        self.evaluator: Optional[ComprehensiveQualityEvaluator] = None

        # Load existing logs
        self._load_logs()

    def _load_logs(self):
        """Load existing logs from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.logs = [QuestionLog(**log) for log in data]
            except Exception as e:
                print(f"[WARNING] Could not load existing logs: {e}")
                self.logs = []

    def _save_logs(self):
        """Save logs to file"""
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(
                    [asdict(log) for log in self.logs], f, indent=2, ensure_ascii=False
                )
        except Exception as e:
            print(f"[ERROR] Could not save logs: {e}")

    async def _get_evaluator(self):
        """Lazy-load evaluator with ÖSYM references"""
        if self.evaluator is None:
            # Load ÖSYM references
            async with AsyncSession(async_engine) as db:
                query = text(
                    """
                    SELECT metin, dogru_cevap, zorluk, konu
                    FROM sorular
                    WHERE dogru_cevap IS NOT NULL
                    AND metin IS NOT NULL
                    LIMIT 30
                """
                )
                result = await db.execute(query)
                rows = result.fetchall()
                osym_questions = [
                    {
                        "question_text": row[0],
                        "correct_answer": row[1],
                        "difficulty": row[2],
                        "topic": row[3],
                    }
                    for row in rows
                ]

            self.evaluator = ComprehensiveQualityEvaluator(
                osym_reference_questions=osym_questions
            )

        return self.evaluator

    async def log_question(
        self,
        question: Dict,
        subject: str,
        topic: str,
        question_id: str,
        enhanced: bool = True,
    ):
        """
        Log a generated question with automatic Wave 2B evaluation

        Args:
            question: Question dict with 'stem', 'options', etc.
            subject: Subject name (e.g., "Matematik", "Türkçe")
            topic: Topic name
            question_id: Unique question identifier
            enhanced: Whether enhanced template was used
        """
        try:
            # Get evaluator
            evaluator = await self._get_evaluator()

            # Evaluate question
            evaluation = evaluator.evaluate(
                question={
                    "question_text": question.get("stem", ""),
                    "subject": subject,
                },
                stage="standard",
            )

            # Create log entry
            log_entry = QuestionLog(
                timestamp=datetime.now().isoformat(),
                subject=subject,
                topic=topic,
                question_id=question_id,
                length=len(question.get("stem", "")),
                wave2b_score=evaluation.overall_score,
                decision=evaluation.decision,
                bloom_level=evaluation.bloom_level,
                enhanced=enhanced,
            )

            # Add to logs
            self.logs.append(log_entry)
            self._save_logs()

            # Check if milestone reached
            await self._check_milestones()

            return evaluation

        except Exception as e:
            print(f"[ERROR] Error logging question: {e}")
            return None

    async def _check_milestones(self):
        """Check if milestone reached and generate report"""
        total = len(self.logs)

        # Generate reports at milestones
        if total in [25, 50, 75, 100]:
            print(f"\n[MILESTONE] {total} questions generated! Generating report...")
            report = await self.generate_report()

            # Save milestone report
            report_file = (
                Path(__file__).parent.parent / f"production_report_{total}_questions.md"
            )
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"[OK] Report saved: {report_file}")

    async def generate_report(self, last_n: Optional[int] = None) -> str:
        """
        Generate production quality report

        Args:
            last_n: Only analyze last N questions (None = all)
        """
        logs = self.logs[-last_n:] if last_n else self.logs

        if not logs:
            return "No questions logged yet."

        # Calculate metrics
        total = len(logs)

        # By subject
        subjects = {}
        for log in logs:
            if log.subject not in subjects:
                subjects[log.subject] = []
            subjects[log.subject].append(log)

        # Overall metrics
        scores = [log.wave2b_score for log in logs]
        approvals = sum(1 for log in logs if log.decision == "APPROVE")
        reviews = sum(1 for log in logs if log.decision == "REVIEW")
        rejects = sum(1 for log in logs if log.decision == "REJECT")

        report = f"""# Production Quality Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Questions**: {total}
**Analysis Period**: {logs[0].timestamp[:10]} to {logs[-1].timestamp[:10]}

---

## Overall Performance

**Quality Metrics**:
- Average Wave 2B Score: **{statistics.mean(scores):.3f}**
- Median Score: **{statistics.median(scores):.3f}**
- Std Deviation: **{statistics.stdev(scores) if len(scores) > 1 else 0:.3f}**
- Min Score: **{min(scores):.3f}**
- Max Score: **{max(scores):.3f}**

**Approval Breakdown**:
- APPROVE: **{approvals}** ({approvals/total*100:.1f}%)
- REVIEW: **{reviews}** ({reviews/total*100:.1f}%)
- REJECT: **{rejects}** ({rejects/total*100:.1f}%)

**Quality Targets**:
- Questions >= 0.85: **{sum(1 for s in scores if s >= 0.85)}** ({sum(1 for s in scores if s >= 0.85)/total*100:.1f}%)
- Approval Rate: **{approvals/total*100:.1f}%** (Target: 75-85%)

---

## Performance by Subject

"""

        # Subject-specific metrics
        for subject, subject_logs in subjects.items():
            subject_scores = [log.wave2b_score for log in subject_logs]
            subject_approvals = sum(
                1 for log in subject_logs if log.decision == "APPROVE"
            )
            subject_reviews = sum(1 for log in subject_logs if log.decision == "REVIEW")
            subject_rejects = sum(1 for log in subject_logs if log.decision == "REJECT")
            avg_length = statistics.mean([log.length for log in subject_logs])
            avg_bloom = statistics.mean([log.bloom_level for log in subject_logs])

            report += f"""### {subject} ({len(subject_logs)} questions)

**Quality**:
- Average Score: **{statistics.mean(subject_scores):.3f}**
- Score Range: {min(subject_scores):.3f} - {max(subject_scores):.3f}

**Decisions**:
- APPROVE: {subject_approvals} ({subject_approvals/len(subject_logs)*100:.1f}%)
- REVIEW: {subject_reviews} ({subject_reviews/len(subject_logs)*100:.1f}%)
- REJECT: {subject_rejects} ({subject_rejects/len(subject_logs)*100:.1f}%)

**Characteristics**:
- Average Length: {avg_length:.0f} characters
- Average Bloom Level: {avg_bloom:.1f}

**Top Topics**:
"""
            # Topic breakdown
            topics = {}
            for log in subject_logs:
                topics[log.topic] = topics.get(log.topic, [])
                topics[log.topic].append(log.wave2b_score)

            for topic, topic_scores in sorted(
                topics.items(), key=lambda x: statistics.mean(x[1]), reverse=True
            )[:5]:
                report += f"- {topic}: {statistics.mean(topic_scores):.3f} avg ({len(topic_scores)} questions)\n"

            report += "\n"

        # Trend analysis
        if total >= 10:
            report += f"""---

## Trend Analysis

**First 10 Questions**:
- Average Score: {statistics.mean([log.wave2b_score for log in logs[:10]]):.3f}
- Approval Rate: {sum(1 for log in logs[:10] if log.decision == 'APPROVE')/10*100:.1f}%

**Last 10 Questions**:
- Average Score: {statistics.mean([log.wave2b_score for log in logs[-10:]]):.3f}
- Approval Rate: {sum(1 for log in logs[-10:] if log.decision == 'APPROVE')/10*100:.1f}%

**Trend**: {'Improving' if statistics.mean([log.wave2b_score for log in logs[-10:]]) > statistics.mean([log.wave2b_score for log in logs[:10]]) else 'Stable/Declining'}

"""

        # Alerts
        report += """---

## Quality Alerts

"""

        # Check for issues
        alerts = []

        if approvals / total < 0.70:
            alerts.append(
                f"[WARNING] Low approval rate ({approvals/total*100:.1f}% < 70%)"
            )

        if statistics.mean(scores) < 0.80:
            alerts.append(
                f"[WARNING] Average quality below target ({statistics.mean(scores):.3f} < 0.80)"
            )

        if rejects / total > 0.10:
            alerts.append(
                f"[WARNING] High reject rate ({rejects/total*100:.1f}% > 10%)"
            )

        # Subject-specific alerts
        for subject, subject_logs in subjects.items():
            subject_scores = [log.wave2b_score for log in subject_logs]
            subject_approvals = sum(
                1 for log in subject_logs if log.decision == "APPROVE"
            )

            if statistics.mean(subject_scores) < 0.75:
                alerts.append(
                    f"[WARNING] {subject} quality low ({statistics.mean(subject_scores):.3f} < 0.75)"
                )

            if subject_approvals / len(subject_logs) < 0.60:
                alerts.append(
                    f"[WARNING] {subject} approval rate low ({subject_approvals/len(subject_logs)*100:.1f}% < 60%)"
                )

        if alerts:
            for alert in alerts:
                report += f"{alert}\n"
        else:
            report += "[OK] All quality metrics within acceptable range!\n"

        report += """
---

## Recommendations

"""

        # Generate recommendations
        if approvals / total >= 0.75 and statistics.mean(scores) >= 0.80:
            report += """[OK] **System Performing Well**
- Continue monitoring
- Enhanced templates working as expected
- No immediate action required

"""
        else:
            report += """[WARNING] **Quality Below Target**

Suggested Actions:
1. Review REVIEW and REJECT questions for common patterns
2. Consider adjusting enhancement templates
3. Check if specific topics are underperforming
4. Monitor for next 25 questions before making changes

"""

        report += f"""---

**Next Milestone**: {((total // 25) + 1) * 25} questions
**Questions Until Next Report**: {((total // 25) + 1) * 25 - total}

**Monitor Status**: ACTIVE
**Enhanced Templates**: {'ENABLED' if any(log.enhanced for log in logs) else 'DISABLED'}
"""

        return report

    def get_stats_summary(self) -> Dict:
        """Get quick stats summary (for API/dashboard)"""
        if not self.logs:
            return {"total": 0, "message": "No questions logged"}

        scores = [log.wave2b_score for log in self.logs]
        approvals = sum(1 for log in self.logs if log.decision == "APPROVE")

        return {
            "total_questions": len(self.logs),
            "average_score": statistics.mean(scores),
            "approval_rate": approvals / len(self.logs) * 100,
            "last_question": self.logs[-1].timestamp,
            "subjects": list(set(log.subject for log in self.logs)),
        }


# Singleton instance
_monitor_instance = None


def get_monitor() -> ProductionQualityMonitor:
    """Get singleton monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ProductionQualityMonitor()
    return _monitor_instance


# Example usage
async def example_usage():
    """Example of how to use the monitor"""
    monitor = get_monitor()

    # Simulate logging a question
    sample_question = {
        "stem": "Bir fonksiyonun türevi...",
        "options": ["A) 1", "B) 2", "C) 3", "D) 4"],
        "correct_answer": "A",
    }

    await monitor.log_question(
        question=sample_question,
        subject="Matematik",
        topic="Türev",
        question_id="test-001",
        enhanced=True,
    )

    # Generate report
    report = await monitor.generate_report()
    print(report)


if __name__ == "__main__":
    asyncio.run(example_usage())
