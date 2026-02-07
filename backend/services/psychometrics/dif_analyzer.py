"""
Differential Item Functioning (DIF) Analysis
Detects bias in test items across demographic groups for fairness
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from scipy import stats

logger = logging.getLogger(__name__)

try:
    from statsmodels.formula.api import logit
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available for DIF analysis")


class DIFAnalyzer:
    """
    Differential Item Functioning (DIF) Analyzer

    Methods:
    - Mantel-Haenszel DIF (non-parametric)
    - Logistic Regression DIF (parametric)
    - Effect size calculation (Delta-MH)
    - Fairness classification (A/B/C)
    """

    def __init__(self):
        # ETS DIF classification thresholds
        self.dif_categories = {
            'A': (0, 1.0),      # Negligible
            'B': (1.0, 1.5),    # Slight to moderate
            'C': (1.5, float('inf'))  # Moderate to large
        }

    def mantel_haenszel_dif(
        self,
        responses: np.ndarray,
        group: np.ndarray,
        ability: np.ndarray
    ) -> Dict[str, Any]:
        """
        Mantel-Haenszel DIF analysis

        Args:
            responses: Item responses (0/1) array [n_students]
            group: Group membership (0=reference, 1=focal) [n_students]
            ability: Ability estimates (total score) [n_students]

        Returns:
            DIF statistics
        """
        # Create ability strata
        n_strata = 10
        strata = self._create_strata(ability, n_strata)

        # Calculate MH statistic
        mh_stat = self._calculate_mh_statistic(responses, group, strata)

        # Calculate Delta-MH (effect size)
        delta_mh = -2.35 * np.log(mh_stat)

        # Classify DIF
        dif_category = self._classify_dif(abs(delta_mh))

        return {
            'mh_statistic': mh_stat,
            'delta_mh': delta_mh,
            'dif_category': dif_category,
            'significant': abs(delta_mh) > 1.0,
            'interpretation': self._interpret_dif(delta_mh, dif_category),
            'method': 'Mantel-Haenszel'
        }

    def logistic_regression_dif(
        self,
        responses: np.ndarray,
        group: np.ndarray,
        ability: np.ndarray
    ) -> Dict[str, Any]:
        """
        Logistic Regression DIF analysis

        Models:
        - Model 1: ability only
        - Model 2: ability + group
        - Model 3: ability + group + interaction

        Args:
            responses: Item responses
            group: Group membership
            ability: Ability estimates

        Returns:
            DIF statistics
        """
        if not STATSMODELS_AVAILABLE:
            raise RuntimeError("statsmodels required for logistic regression DIF")

        import pandas as pd

        # Prepare data
        data = pd.DataFrame({
            'response': responses,
            'ability': ability,
            'group': group
        })

        try:
            # Model 1: Ability only
            model1 = logit('response ~ ability', data=data).fit(disp=0)
            ll1 = model1.llf

            # Model 2: Ability + Group (uniform DIF)
            model2 = logit('response ~ ability + group', data=data).fit(disp=0)
            ll2 = model2.llf

            # Model 3: Ability + Group + Interaction (non-uniform DIF)
            model3 = logit('response ~ ability + group + ability:group', data=data).fit(disp=0)
            ll3 = model3.llf

            # Likelihood ratio tests
            lr_uniform = 2 * (ll2 - ll1)  # Tests uniform DIF
            lr_nonuniform = 2 * (ll3 - ll2)  # Tests non-uniform DIF

            # Chi-square tests
            p_uniform = 1 - stats.chi2.cdf(lr_uniform, df=1)
            p_nonuniform = 1 - stats.chi2.cdf(lr_nonuniform, df=1)

            # Effect size (R-squared difference)
            r2_diff = self._pseudo_r2(ll2) - self._pseudo_r2(ll1)

            return {
                'uniform_dif_lr': lr_uniform,
                'uniform_dif_p': p_uniform,
                'nonuniform_dif_lr': lr_nonuniform,
                'nonuniform_dif_p': p_nonuniform,
                'effect_size': r2_diff,
                'has_uniform_dif': p_uniform < 0.05,
                'has_nonuniform_dif': p_nonuniform < 0.05,
                'method': 'Logistic Regression'
            }

        except Exception as e:
            logger.error(f"Logistic regression DIF failed: {e}")
            return {'error': str(e)}

    def analyze_item_dif(
        self,
        item_responses: Dict[int, np.ndarray],
        groups: np.ndarray,
        ability_scores: np.ndarray,
        method: str = 'both'
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze DIF for multiple items

        Args:
            item_responses: {item_id: response_array}
            groups: Group membership array
            ability_scores: Total test scores
            method: 'mh', 'lr', or 'both'

        Returns:
            DIF results for each item
        """
        results = {}

        for item_id, responses in item_responses.items():
            item_results = {}

            if method in ['mh', 'both']:
                item_results['mh'] = self.mantel_haenszel_dif(
                    responses, groups, ability_scores
                )

            if method in ['lr', 'both'] and STATSMODELS_AVAILABLE:
                item_results['lr'] = self.logistic_regression_dif(
                    responses, groups, ability_scores
                )

            results[item_id] = item_results

        return results

    def generate_fairness_report(
        self,
        dif_results: Dict[int, Dict[str, Any]],
        item_metadata: Optional[Dict[int, Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive fairness report

        Args:
            dif_results: DIF analysis results
            item_metadata: Optional item information

        Returns:
            Fairness report
        """
        flagged_items = []
        category_counts = {'A': 0, 'B': 0, 'C': 0}

        for item_id, results in dif_results.items():
            if 'mh' in results:
                category = results['mh']['dif_category']
                category_counts[category] += 1

                if category in ['B', 'C']:
                    flagged_items.append({
                        'item_id': item_id,
                        'category': category,
                        'delta_mh': results['mh']['delta_mh'],
                        'metadata': item_metadata.get(item_id, {}) if item_metadata else {}
                    })

        return {
            'total_items': len(dif_results),
            'category_distribution': category_counts,
            'flagged_items': flagged_items,
            'flagged_count': len(flagged_items),
            'pass_rate': category_counts['A'] / len(dif_results) if dif_results else 0,
            'recommendations': self._generate_fairness_recommendations(flagged_items)
        }

    def _create_strata(self, ability: np.ndarray, n_strata: int) -> np.ndarray:
        """Create ability strata for MH analysis"""
        percentiles = np.linspace(0, 100, n_strata + 1)
        bins = np.percentile(ability, percentiles)
        strata = np.digitize(ability, bins[1:-1])
        return strata

    def _calculate_mh_statistic(
        self,
        responses: np.ndarray,
        group: np.ndarray,
        strata: np.ndarray
    ) -> float:
        """Calculate Mantel-Haenszel statistic"""
        mh_numerator = 0
        mh_denominator = 0

        for k in np.unique(strata):
            mask = strata == k

            # Reference group (0)
            r0 = responses[mask & (group == 0)]
            n0 = len(r0)
            s0 = np.sum(r0)

            # Focal group (1)
            r1 = responses[mask & (group == 1)]
            n1 = len(r1)
            s1 = np.sum(r1)

            if n0 > 0 and n1 > 0:
                n_total = n0 + n1
                s_total = s0 + s1

                mh_numerator += (s0 * n1) / n_total
                mh_denominator += (s1 * n0) / n_total

        mh_stat = mh_numerator / mh_denominator if mh_denominator > 0 else 1.0
        return mh_stat

    def _classify_dif(self, delta_mh: float) -> str:
        """Classify DIF magnitude (A/B/C)"""
        abs_delta = abs(delta_mh)

        for category, (min_val, max_val) in self.dif_categories.items():
            if min_val <= abs_delta < max_val:
                return category

        return 'C'

    def _interpret_dif(self, delta_mh: float, category: str) -> str:
        """Interpret DIF results"""
        direction = "favors focal group" if delta_mh > 0 else "favors reference group"

        interpretations = {
            'A': f"Negligible DIF ({direction})",
            'B': f"Slight to moderate DIF ({direction}) - Review recommended",
            'C': f"Moderate to large DIF ({direction}) - Item should be reviewed or removed"
        }

        return interpretations.get(category, "Unknown")

    def _pseudo_r2(self, log_likelihood: float) -> float:
        """Calculate pseudo R-squared (McFadden)"""
        # Simplified - actual implementation would need null model LL
        return abs(log_likelihood) / 1000  # Placeholder

    def _generate_fairness_recommendations(self, flagged_items: List[Dict]) -> List[str]:
        """Generate recommendations based on flagged items"""
        recommendations = []

        if not flagged_items:
            recommendations.append("All items show negligible DIF - test appears fair")
            return recommendations

        c_count = sum(1 for item in flagged_items if item['category'] == 'C')
        b_count = len(flagged_items) - c_count

        if c_count > 0:
            recommendations.append(
                f"{c_count} items show large DIF - consider removing or revising"
            )

        if b_count > 0:
            recommendations.append(
                f"{b_count} items show moderate DIF - expert review recommended"
            )

        if len(flagged_items) / 10 > 0.2:  # More than 20% flagged
            recommendations.append(
                "High proportion of flagged items - review test construction process"
            )

        return recommendations