"""
Distractor Analysis Service
Analyzes effectiveness of wrong answer options (distractors)
"""

import numpy as np
from typing import List, Dict, Any
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class DistractorAnalyzer:
    """
    Distractor Effectiveness Analyzer

    Metrics:
    - Point-biserial correlation per option
    - P-values (proportion selecting each option)
    - Distractor efficiency
    - Recommendations for improvement
    """

    def __init__(self):
        # Quality thresholds
        self.thresholds = {
            'min_selection_rate': 0.05,  # At least 5% should select
            'max_selection_rate': 0.40,  # No more than 40% (unless correct)
            'min_discrimination': -0.10,  # Negative correlation expected
            'effective_distractor_count': 3  # At least 3 effective distractors
        }

    def analyze_distractor(
        self,
        responses: np.ndarray,
        correct_answer: str,
        total_scores: np.ndarray,
        options: List[str] = ['A', 'B', 'C', 'D', 'E']
    ) -> Dict[str, Any]:
        """
        Analyze distractor effectiveness for a question

        Args:
            responses: Student responses (option letters)
            correct_answer: Correct option letter
            total_scores: Total test scores for ability estimate
            options: List of option letters

        Returns:
            Distractor analysis results
        """
        results = {
            'correct_answer': correct_answer,
            'options': {},
            'summary': {}
        }

        # Analyze each option
        for option in options:
            option_analysis = self._analyze_single_option(
                responses,
                option,
                option == correct_answer,
                total_scores
            )
            results['options'][option] = option_analysis

        # Generate summary
        results['summary'] = self._generate_summary(results['options'], correct_answer)

        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)

        return results

    def _analyze_single_option(
        self,
        responses: np.ndarray,
        option: str,
        is_correct: bool,
        total_scores: np.ndarray
    ) -> Dict[str, Any]:
        """Analyze a single option"""

        # Binary coding: 1 if selected, 0 otherwise
        selected = (responses == option).astype(int)

        # Count
        n_selected = np.sum(selected)
        n_total = len(responses)
        selection_rate = n_selected / n_total if n_total > 0 else 0

        # Point-biserial correlation
        if n_selected > 0 and n_selected < n_total:
            rpb = self._point_biserial(selected, total_scores)
        else:
            rpb = 0.0

        # Expected: positive for correct, negative for distractors
        expected_sign = 1 if is_correct else -1
        correct_sign = (np.sign(rpb) == expected_sign) or (rpb == 0)

        # Effectiveness rating
        effectiveness = self._rate_option_effectiveness(
            selection_rate,
            rpb,
            is_correct
        )

        return {
            'option': option,
            'is_correct': is_correct,
            'n_selected': int(n_selected),
            'selection_rate': float(selection_rate),
            'point_biserial': float(rpb),
            'correct_sign': correct_sign,
            'effectiveness': effectiveness,
            'flagged': self._should_flag_option(selection_rate, rpb, is_correct)
        }

    def _point_biserial(self, binary: np.ndarray, continuous: np.ndarray) -> float:
        """Calculate point-biserial correlation"""
        try:
            corr, _ = stats.pointbiserialr(binary, continuous)
            return corr if not np.isnan(corr) else 0.0
        except (ValueError, TypeError, RuntimeWarning) as e:
            logger.debug(f"Point-biserial correlation failed: {e}")
            return 0.0

    def _rate_option_effectiveness(
        self,
        selection_rate: float,
        rpb: float,
        is_correct: bool
    ) -> str:
        """Rate option effectiveness"""

        if is_correct:
            # Correct answer evaluation
            if selection_rate > 0.7 and rpb > 0.3:
                return "Excellent"
            elif selection_rate > 0.5 and rpb > 0.2:
                return "Good"
            elif selection_rate > 0.3:
                return "Fair"
            else:
                return "Poor - Too difficult"
        else:
            # Distractor evaluation
            if (selection_rate >= self.thresholds['min_selection_rate'] and
                selection_rate <= self.thresholds['max_selection_rate'] and
                rpb < 0):
                return "Effective"
            elif selection_rate < self.thresholds['min_selection_rate']:
                return "Ineffective - Rarely selected"
            elif selection_rate > self.thresholds['max_selection_rate']:
                return "Problematic - Too attractive"
            else:
                return "Poor discrimination"

    def _should_flag_option(
        self,
        selection_rate: float,
        rpb: float,
        is_correct: bool
    ) -> bool:
        """Determine if option should be flagged for review"""

        if is_correct:
            # Flag if correct answer is too easy or too hard
            if selection_rate < 0.2 or selection_rate > 0.95:
                return True
            if rpb < 0:  # Negative discrimination for correct answer
                return True
        else:
            # Flag if distractor is not working
            if selection_rate < self.thresholds['min_selection_rate']:
                return True  # Never selected
            if selection_rate > self.thresholds['max_selection_rate']:
                return True  # More attractive than correct
            if rpb > 0.1:  # Positive correlation (higher ability students selecting wrong)
                return True

        return False

    def _generate_summary(
        self,
        options_analysis: Dict[str, Dict],
        correct_answer: str
    ) -> Dict[str, Any]:
        """Generate summary statistics"""

        # Count effective distractors
        effective_distractors = sum(
            1 for opt, data in options_analysis.items()
            if not data['is_correct'] and data['effectiveness'] == "Effective"
        )

        # Count flagged options
        flagged_count = sum(
            1 for data in options_analysis.values()
            if data['flagged']
        )

        # Get correct answer stats
        correct_stats = options_analysis[correct_answer]

        return {
            'effective_distractors': effective_distractors,
            'total_distractors': len(options_analysis) - 1,
            'distractor_quality': self._classify_distractor_quality(effective_distractors),
            'flagged_options': flagged_count,
            'correct_answer_p_value': correct_stats['selection_rate'],
            'correct_answer_discrimination': correct_stats['point_biserial'],
            'overall_quality': self._classify_overall_quality(
                effective_distractors,
                correct_stats['selection_rate'],
                correct_stats['point_biserial']
            )
        }

    def _classify_distractor_quality(self, effective_count: int) -> str:
        """Classify overall distractor quality"""
        if effective_count >= self.thresholds['effective_distractor_count']:
            return "Good"
        elif effective_count >= 2:
            return "Fair"
        else:
            return "Poor"

    def _classify_overall_quality(
        self,
        effective_distractors: int,
        p_value: float,
        discrimination: float
    ) -> str:
        """Classify overall question quality"""

        if (effective_distractors >= 3 and
            0.3 <= p_value <= 0.8 and
            discrimination > 0.3):
            return "Excellent"
        elif (effective_distractors >= 2 and
              0.2 <= p_value <= 0.9 and
              discrimination > 0.2):
            return "Good"
        elif effective_distractors >= 1:
            return "Fair"
        else:
            return "Poor - Needs revision"

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        summary = results['summary']
        options = results['options']

        # Check overall quality
        if summary['overall_quality'] in ['Poor - Needs revision', 'Fair']:
            recommendations.append(
                f"Question quality is {summary['overall_quality']} - consider revision"
            )

        # Check distractor effectiveness
        if summary['effective_distractors'] < self.thresholds['effective_distractor_count']:
            recommendations.append(
                f"Only {summary['effective_distractors']}/4 distractors are effective - "
                "improve weak distractors"
            )

        # Check specific options
        for opt, data in options.items():
            if data['flagged']:
                if data['is_correct']:
                    if data['selection_rate'] < 0.2:
                        recommendations.append(
                            f"Correct answer ({opt}) selected by <20% - question may be too difficult"
                        )
                    elif data['selection_rate'] > 0.95:
                        recommendations.append(
                            f"Correct answer ({opt}) selected by >95% - question may be too easy"
                        )
                    if data['point_biserial'] < 0:
                        recommendations.append(
                            f"Correct answer ({opt}) has negative discrimination - review question"
                        )
                else:
                    if data['selection_rate'] < self.thresholds['min_selection_rate']:
                        recommendations.append(
                            f"Distractor {opt} rarely selected (<5%) - replace with more plausible option"
                        )
                    if data['selection_rate'] > self.thresholds['max_selection_rate']:
                        recommendations.append(
                            f"Distractor {opt} too attractive (>{self.thresholds['max_selection_rate']*100}%) - "
                            "may be ambiguous or partially correct"
                        )
                    if data['point_biserial'] > 0.1:
                        recommendations.append(
                            f"Distractor {opt} attracts high-ability students - review for correctness"
                        )

        if not recommendations:
            recommendations.append("All distractors functioning well - no changes needed")

        return recommendations

    def batch_analyze(
        self,
        item_responses: Dict[int, np.ndarray],
        correct_answers: Dict[int, str],
        total_scores: np.ndarray
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze distractors for multiple items

        Args:
            item_responses: {item_id: response_array}
            correct_answers: {item_id: correct_answer}
            total_scores: Total test scores

        Returns:
            Distractor analyses for each item
        """
        results = {}

        for item_id, responses in item_responses.items():
            correct = correct_answers.get(item_id)

            if correct:
                results[item_id] = self.analyze_distractor(
                    responses,
                    correct,
                    total_scores
                )

        return results

    def generate_improvement_report(
        self,
        analyses: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate improvement report for test"""

        priority_revisions = []
        suggested_improvements = []

        for item_id, analysis in analyses.items():
            quality = analysis['summary']['overall_quality']

            if quality == "Poor - Needs revision":
                priority_revisions.append({
                    'item_id': item_id,
                    'reason': 'Poor overall quality',
                    'recommendations': analysis['recommendations']
                })
            elif quality == "Fair":
                suggested_improvements.append({
                    'item_id': item_id,
                    'recommendations': analysis['recommendations']
                })

        return {
            'total_items': len(analyses),
            'priority_revisions': priority_revisions,
            'priority_count': len(priority_revisions),
            'suggested_improvements': suggested_improvements,
            'suggested_count': len(suggested_improvements),
            'quality_distribution': self._get_quality_distribution(analyses)
        }

    def _get_quality_distribution(self, analyses: Dict) -> Dict[str, int]:
        """Get distribution of quality ratings"""
        distribution = {
            'Excellent': 0,
            'Good': 0,
            'Fair': 0,
            'Poor - Needs revision': 0
        }

        for analysis in analyses.values():
            quality = analysis['summary']['overall_quality']
            distribution[quality] = distribution.get(quality, 0) + 1

        return distribution