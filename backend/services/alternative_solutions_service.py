"""
Alternatif Çözüm Yolları Servisi
Task 73.1: Çoklu Çözüm Desteği

- Multiple solution storage
- Solution categorization
- Difficulty comparison
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question_bank import QuestionBankItem

logger = logging.getLogger(__name__)


class AlternativeSolutionsService:
    """
    Alternatif çözüm yolları servisi
    REQ-13.1: Makale/Soru içerik yönetimi - Alternatif çözümler
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ========================================================================
    # TASK 73.1: Çoklu Çözüm Desteği
    # ========================================================================

    async def add_solution(
        self,
        question_id: str,
        solution_data: Dict[str, Any],
        created_by: str,
    ) -> Dict[str, Any]:
        """
        Soruya alternatif çözüm ekle

        Args:
            question_id: Soru ID'si
            solution_data: Çözüm verileri
            created_by: Oluşturan kullanıcı ID

        Returns:
            Dict: İşlem sonucu
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return {"success": False, "message": "Soru bulunamadı"}

            # Mevcut çözümleri al
            current_solutions = question.alternative_solutions or {}
            if not isinstance(current_solutions, dict):
                current_solutions = {}

            # Yeni çözüm ID'si oluştur
            solution_id = str(uuid.uuid4())

            # Çözüm nesnesini oluştur
            new_solution = {
                "id": solution_id,
                "title": solution_data.get("title"),
                "category": solution_data.get("category"),
                "difficulty": solution_data.get("difficulty"),
                "estimated_time_seconds": solution_data.get("estimated_time_seconds"),
                "steps": solution_data.get("steps", []),
                "tips": solution_data.get("tips", []),
                "prerequisites": solution_data.get("prerequisites", []),
                "advantages": solution_data.get("advantages", []),
                "disadvantages": solution_data.get("disadvantages", []),
                "video_url": solution_data.get("video_url"),
                "created_by": created_by,
                "created_by_type": solution_data.get("created_by_type", "teacher"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "votes": {"upvotes": 0, "downvotes": 0, "total": 0},
                "usage_count": 0,
                "is_active": True,
            }

            # Çözümleri güncelle
            if "solutions" not in current_solutions:
                current_solutions["solutions"] = []

            current_solutions["solutions"].append(new_solution)

            # Veritabanını güncelle
            question.alternative_solutions = current_solutions
            question.updated_at = datetime.now()

            await self.db.commit()
            await self.db.refresh(question)

            logger.info(f"Alternatif çözüm eklendi: {solution_id} -> {question_id}")

            return {
                "success": True,
                "solution_id": solution_id,
                "message": "Çözüm başarıyla eklendi",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Çözüm ekleme hatası: {str(e)}")
            raise

    async def get_solutions(
        self,
        question_id: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        sort_by: str = "difficulty",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Sorunun alternatif çözümlerini getir

        Args:
            question_id: Soru ID'si
            category: Kategori filtresi
            difficulty: Zorluk filtresi
            sort_by: Sıralama kriteri

        Returns:
            List[Dict]: Çözüm listesi
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return None

            # Çözümleri al
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Aktif çözümleri filtrele
            solutions = [s for s in solutions if s.get("is_active", True)]

            # Kategori filtresi
            if category:
                solutions = [s for s in solutions if s.get("category") == category]

            # Zorluk filtresi
            if difficulty:
                solutions = [s for s in solutions if s.get("difficulty") == difficulty]

            # Sıralama
            solutions = self._sort_solutions(solutions, sort_by)

            return solutions

        except Exception as e:
            logger.error(f"Çözüm getirme hatası: {str(e)}")
            return []

    async def get_solution_by_id(
        self, question_id: str, solution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Belirli bir çözümü getir

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si

        Returns:
            Dict: Çözüm detayları
        """
        try:
            solutions = await self.get_solutions(question_id)

            if not solutions:
                return None

            for solution in solutions:
                if solution.get("id") == solution_id:
                    return solution

            return None

        except Exception as e:
            logger.error(f"Çözüm detay hatası: {str(e)}")
            return None

    async def update_solution(
        self,
        question_id: str,
        solution_id: str,
        update_data: Dict[str, Any],
        updated_by: str,
    ) -> bool:
        """
        Çözümü güncelle

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si
            update_data: Güncellenecek veriler
            updated_by: Güncelleyen kullanıcı ID

        Returns:
            bool: Başarılı mı
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return False

            # Çözümleri al
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Çözümü bul ve güncelle
            updated = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    # Güncelleme yap
                    for key, value in update_data.items():
                        solution[key] = value

                    solution["updated_at"] = datetime.now().isoformat()
                    solution["updated_by"] = updated_by
                    updated = True
                    break

            if not updated:
                return False

            # Veritabanını güncelle
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Çözüm güncellendi: {solution_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Çözüm güncelleme hatası: {str(e)}")
            return False

    async def delete_solution(
        self, question_id: str, solution_id: str, deleted_by: str
    ) -> bool:
        """
        Çözümü sil (soft delete)

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si
            deleted_by: Silen kullanıcı ID

        Returns:
            bool: Başarılı mı
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return False

            # Çözümleri al
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Çözümü bul ve deaktif et
            deleted = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    solution["is_active"] = False
                    solution["deleted_at"] = datetime.now().isoformat()
                    solution["deleted_by"] = deleted_by
                    deleted = True
                    break

            if not deleted:
                return False

            # Veritabanını güncelle
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Çözüm silindi: {solution_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Çözüm silme hatası: {str(e)}")
            return False

    # ========================================================================
    # Çözüm Karşılaştırma ve Analiz
    # ========================================================================

    async def compare_solutions(
        self, question_id: str, solution_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Birden fazla çözümü karşılaştır (TASK 73.2: Enhanced Comparison)

        Özellikler:
        - Side-by-side comparison (yan yana karşılaştırma)
        - Step-by-step breakdown (adım adım detay)
        - Time complexity analysis (zaman karmaşıklığı analizi)

        Args:
            question_id: Soru ID'si
            solution_ids: Karşılaştırılacak çözüm ID'leri

        Returns:
            Dict: Gelişmiş karşılaştırma sonuçları
        """
        try:
            solutions = await self.get_solutions(question_id)

            if not solutions:
                return None

            # Seçili çözümleri filtrele
            selected_solutions = [s for s in solutions if s.get("id") in solution_ids]

            if not selected_solutions:
                return None

            # Karşılaştırma metrikleri
            comparison = {
                "question_id": question_id,
                "comparison_type": "side_by_side",
                "solutions": [],
                "side_by_side": {
                    "headers": [],
                    "metrics": {},
                    "steps_comparison": [],
                },
                "step_by_step_breakdown": [],
                "time_complexity_analysis": {},
                "summary": {
                    "easiest": None,
                    "fastest": None,
                    "most_efficient": None,
                    "most_popular": None,
                    "most_detailed": None,
                    "recommended": None,
                },
            }

            # Her çözüm için detaylar
            for solution in selected_solutions:
                solution_info = {
                    "id": solution.get("id"),
                    "title": solution.get("title"),
                    "category": solution.get("category"),
                    "difficulty": solution.get("difficulty"),
                    "difficulty_score": self._get_difficulty_score(
                        solution.get("difficulty")
                    ),
                    "estimated_time_seconds": solution.get("estimated_time_seconds"),
                    "step_count": len(solution.get("steps", [])),
                    "steps": solution.get("steps", []),
                    "advantages": solution.get("advantages", []),
                    "disadvantages": solution.get("disadvantages", []),
                    "votes": solution.get("votes", {}),
                    "usage_count": solution.get("usage_count", 0),
                    "prerequisites": solution.get("prerequisites", []),
                    "tips": solution.get("tips", []),
                }
                comparison["solutions"].append(solution_info)

            # TASK 73.2.1: Side-by-side comparison
            comparison["side_by_side"] = self._build_side_by_side_comparison(
                comparison["solutions"]
            )

            # TASK 73.2.2: Step-by-step breakdown
            comparison["step_by_step_breakdown"] = self._build_step_by_step_breakdown(
                comparison["solutions"]
            )

            # TASK 73.2.3: Time complexity analysis
            comparison["time_complexity_analysis"] = self._analyze_time_complexity(
                comparison["solutions"]
            )

            # Özet istatistikler (geliştirilmiş)
            if comparison["solutions"]:
                # En kolay
                easiest = min(
                    comparison["solutions"], key=lambda x: x["difficulty_score"]
                )
                comparison["summary"]["easiest"] = {
                    "id": easiest["id"],
                    "title": easiest["title"],
                    "difficulty": easiest["difficulty"],
                    "reason": "En düşük zorluk seviyesi",
                }

                # En hızlı
                fastest = min(
                    comparison["solutions"], key=lambda x: x["estimated_time_seconds"]
                )
                comparison["summary"]["fastest"] = {
                    "id": fastest["id"],
                    "title": fastest["title"],
                    "time": fastest["estimated_time_seconds"],
                    "reason": "En kısa çözüm süresi",
                }

                # En verimli (zaman karmaşıklığı bazlı)
                most_efficient = self._find_most_efficient_solution(
                    comparison["solutions"], comparison["time_complexity_analysis"]
                )
                comparison["summary"]["most_efficient"] = most_efficient

                # En popüler
                most_popular = max(
                    comparison["solutions"],
                    key=lambda x: x["votes"].get("total", 0),
                )
                comparison["summary"]["most_popular"] = {
                    "id": most_popular["id"],
                    "title": most_popular["title"],
                    "votes": most_popular["votes"].get("total", 0),
                    "reason": "En çok oy alan çözüm",
                }

                # En detaylı
                most_detailed = max(
                    comparison["solutions"], key=lambda x: x["step_count"]
                )
                comparison["summary"]["most_detailed"] = {
                    "id": most_detailed["id"],
                    "title": most_detailed["title"],
                    "steps": most_detailed["step_count"],
                    "reason": "En fazla adım içeren çözüm",
                }

                # Önerilen çözüm (çok kriterli)
                comparison["summary"]["recommended"] = self._recommend_solution(
                    comparison["solutions"], comparison["time_complexity_analysis"]
                )

            return comparison

        except Exception as e:
            logger.error(f"Karşılaştırma hatası: {str(e)}")
            return None

    def _build_side_by_side_comparison(
        self, solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        TASK 73.2.1: Yan yana karşılaştırma tablosu oluştur

        Args:
            solutions: Çözüm listesi

        Returns:
            Dict: Yan yana karşılaştırma verileri
        """
        headers = [sol["title"] for sol in solutions]

        metrics = {
            "Zorluk Seviyesi": [sol["difficulty"] for sol in solutions],
            "Tahmini Süre (saniye)": [
                sol["estimated_time_seconds"] for sol in solutions
            ],
            "Adım Sayısı": [sol["step_count"] for sol in solutions],
            "Kategori": [sol["category"] for sol in solutions],
            "Oy Sayısı": [sol["votes"].get("total", 0) for sol in solutions],
            "Kullanım Sayısı": [sol["usage_count"] for sol in solutions],
            "Ön Gereksinim Sayısı": [len(sol["prerequisites"]) for sol in solutions],
            "Avantaj Sayısı": [len(sol["advantages"]) for sol in solutions],
            "Dezavantaj Sayısı": [len(sol["disadvantages"]) for sol in solutions],
            "İpucu Sayısı": [len(sol["tips"]) for sol in solutions],
        }

        # Adım karşılaştırması
        max_steps = max(sol["step_count"] for sol in solutions)
        steps_comparison = []

        for step_num in range(max_steps):
            step_row = {"step_number": step_num + 1, "solutions": []}

            for sol in solutions:
                steps = sol.get("steps", [])
                if step_num < len(steps):
                    step_row["solutions"].append(
                        {
                            "solution_id": sol["id"],
                            "description": steps[step_num].get("description", ""),
                            "formula": steps[step_num].get("formula"),
                            "explanation": steps[step_num].get("explanation"),
                        }
                    )
                else:
                    step_row["solutions"].append(
                        {
                            "solution_id": sol["id"],
                            "description": "—",
                            "formula": None,
                            "explanation": None,
                        }
                    )

            steps_comparison.append(step_row)

        return {
            "headers": headers,
            "metrics": metrics,
            "steps_comparison": steps_comparison,
        }

    def _build_step_by_step_breakdown(
        self, solutions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        TASK 73.2.2: Adım adım detaylı karşılaştırma

        Args:
            solutions: Çözüm listesi

        Returns:
            List[Dict]: Adım adım breakdown
        """
        breakdown = []

        for solution in solutions:
            solution_breakdown = {
                "solution_id": solution["id"],
                "title": solution["title"],
                "total_steps": solution["step_count"],
                "steps": [],
                "flow_analysis": {
                    "linear_steps": 0,
                    "conditional_steps": 0,
                    "iterative_steps": 0,
                },
            }

            for idx, step in enumerate(solution.get("steps", []), 1):
                step_detail = {
                    "step_number": idx,
                    "description": step.get("description", ""),
                    "formula": step.get("formula"),
                    "explanation": step.get("explanation"),
                    "type": self._classify_step_type(step.get("description", "")),
                    "estimated_time_seconds": solution["estimated_time_seconds"]
                    / solution["step_count"]
                    if solution["step_count"] > 0
                    else 0,
                }

                # Adım tipini say
                if step_detail["type"] == "linear":
                    solution_breakdown["flow_analysis"]["linear_steps"] += 1
                elif step_detail["type"] == "conditional":
                    solution_breakdown["flow_analysis"]["conditional_steps"] += 1
                elif step_detail["type"] == "iterative":
                    solution_breakdown["flow_analysis"]["iterative_steps"] += 1

                solution_breakdown["steps"].append(step_detail)

            # Akış analizi yüzdeleri
            total = solution["step_count"]
            if total > 0:
                solution_breakdown["flow_analysis"]["linear_percentage"] = (
                    solution_breakdown["flow_analysis"]["linear_steps"] / total * 100
                )
                solution_breakdown["flow_analysis"]["conditional_percentage"] = (
                    solution_breakdown["flow_analysis"]["conditional_steps"]
                    / total
                    * 100
                )
                solution_breakdown["flow_analysis"]["iterative_percentage"] = (
                    solution_breakdown["flow_analysis"]["iterative_steps"] / total * 100
                )

            breakdown.append(solution_breakdown)

        return breakdown

    def _analyze_time_complexity(
        self, solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        TASK 73.2.3: Zaman karmaşıklığı analizi (Big O notation)

        Args:
            solutions: Çözüm listesi

        Returns:
            Dict: Zaman karmaşıklığı analizi
        """
        analysis = {
            "solutions": [],
            "comparison": {
                "best_case": None,
                "average_case": None,
                "worst_case": None,
            },
            "complexity_ranking": [],
        }

        complexity_order = {
            "O(1)": 1,
            "O(log n)": 2,
            "O(n)": 3,
            "O(n log n)": 4,
            "O(n²)": 5,
            "O(n³)": 6,
            "O(2^n)": 7,
            "O(n!)": 8,
        }

        for solution in solutions:
            # Adım sayısı ve kategoriye göre karmaşıklık tahmini
            complexity = self._estimate_complexity(solution)

            solution_complexity = {
                "solution_id": solution["id"],
                "title": solution["title"],
                "time_complexity": complexity["notation"],
                "space_complexity": complexity["space_notation"],
                "complexity_score": complexity_order.get(complexity["notation"], 5),
                "explanation": complexity["explanation"],
                "operations_count": complexity["operations"],
                "best_case": complexity["best_case"],
                "average_case": complexity["average_case"],
                "worst_case": complexity["worst_case"],
                "scalability": complexity["scalability"],
            }

            analysis["solutions"].append(solution_complexity)

        # En iyi karmaşıklıkları bul
        if analysis["solutions"]:
            best_complexity = min(
                analysis["solutions"], key=lambda x: x["complexity_score"]
            )
            analysis["comparison"]["best_case"] = {
                "solution_id": best_complexity["solution_id"],
                "title": best_complexity["title"],
                "complexity": best_complexity["time_complexity"],
                "reason": "En düşük zaman karmaşıklığı",
            }

            # Karmaşıklık sıralaması
            analysis["complexity_ranking"] = sorted(
                analysis["solutions"], key=lambda x: x["complexity_score"]
            )

        return analysis

    def _classify_step_type(self, description: str) -> str:
        """
        Adım tipini sınıflandır

        Args:
            description: Adım açıklaması

        Returns:
            str: Adım tipi (linear, conditional, iterative)
        """
        description_lower = description.lower()

        # Döngü anahtar kelimeleri
        iterative_keywords = [
            "döngü",
            "tekrar",
            "her",
            "tüm",
            "loop",
            "iterate",
            "for",
            "while",
        ]
        if any(keyword in description_lower for keyword in iterative_keywords):
            return "iterative"

        # Koşul anahtar kelimeleri
        conditional_keywords = [
            "eğer",
            "ise",
            "durumunda",
            "if",
            "else",
            "case",
            "when",
        ]
        if any(keyword in description_lower for keyword in conditional_keywords):
            return "conditional"

        # Varsayılan: doğrusal
        return "linear"

    def _estimate_complexity(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Çözümün zaman karmaşıklığını tahmin et

        Args:
            solution: Çözüm verisi

        Returns:
            Dict: Karmaşıklık bilgileri
        """
        step_count = solution["step_count"]
        category = solution["category"]

        # Kategori bazlı karmaşıklık tahmini
        if category == "hızlı" or category == "formül":
            # Formül bazlı çözümler genellikle O(1)
            return {
                "notation": "O(1)",
                "space_notation": "O(1)",
                "explanation": "Sabit zamanlı çözüm - formül veya hızlı yöntem kullanır",
                "operations": step_count,
                "best_case": "O(1)",
                "average_case": "O(1)",
                "worst_case": "O(1)",
                "scalability": "Mükemmel - problem boyutundan bağımsız",
            }
        elif category == "klasik":
            # Klasik çözümler genellikle O(n)
            return {
                "notation": "O(n)",
                "space_notation": "O(1)",
                "explanation": "Doğrusal zamanlı çözüm - standart adım adım yaklaşım",
                "operations": step_count,
                "best_case": "O(n)",
                "average_case": "O(n)",
                "worst_case": "O(n)",
                "scalability": "İyi - problem boyutu ile doğrusal artar",
            }
        elif category == "görsel":
            # Görsel çözümler değişken
            return {
                "notation": "O(n)",
                "space_notation": "O(n)",
                "explanation": "Görsel temsil gerektiren çözüm - ek bellek kullanır",
                "operations": step_count,
                "best_case": "O(n)",
                "average_case": "O(n)",
                "worst_case": "O(n)",
                "scalability": "İyi - ancak bellek kullanımı artar",
            }
        elif category == "mantıksal":
            # Mantıksal çözümler genellikle verimli
            return {
                "notation": "O(log n)",
                "space_notation": "O(1)",
                "explanation": "Logaritmik zamanlı çözüm - mantıksal kısayollar kullanır",
                "operations": step_count,
                "best_case": "O(1)",
                "average_case": "O(log n)",
                "worst_case": "O(n)",
                "scalability": "Çok iyi - problem boyutu ile yavaş artar",
            }
        else:
            # Varsayılan: adım sayısına göre
            if step_count <= 3:
                notation = "O(1)"
                scalability = "Mükemmel"
            elif step_count <= 10:
                notation = "O(n)"
                scalability = "İyi"
            else:
                notation = "O(n²)"
                scalability = "Orta - büyük problemlerde yavaşlayabilir"

            return {
                "notation": notation,
                "space_notation": "O(1)",
                "explanation": f"Tahmini karmaşıklık - {step_count} adım içerir",
                "operations": step_count,
                "best_case": notation,
                "average_case": notation,
                "worst_case": notation,
                "scalability": scalability,
            }

    def _find_most_efficient_solution(
        self, solutions: List[Dict[str, Any]], complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        En verimli çözümü bul (zaman karmaşıklığı bazlı)

        Args:
            solutions: Çözüm listesi
            complexity_analysis: Karmaşıklık analizi

        Returns:
            Dict: En verimli çözüm bilgisi
        """
        if not complexity_analysis.get("solutions"):
            return None

        most_efficient = min(
            complexity_analysis["solutions"], key=lambda x: x["complexity_score"]
        )

        return {
            "id": most_efficient["solution_id"],
            "title": most_efficient["title"],
            "complexity": most_efficient["time_complexity"],
            "reason": f"En düşük zaman karmaşıklığı ({most_efficient['time_complexity']})",
            "scalability": most_efficient["scalability"],
        }

    def _recommend_solution(
        self, solutions: List[Dict[str, Any]], complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Çok kriterli çözüm önerisi

        Kriterler:
        - Zorluk seviyesi (30%)
        - Zaman karmaşıklığı (30%)
        - Çözüm süresi (20%)
        - Popülerlik (20%)

        Args:
            solutions: Çözüm listesi
            complexity_analysis: Karmaşıklık analizi

        Returns:
            Dict: Önerilen çözüm
        """
        if not solutions:
            return None

        # Her çözüm için skor hesapla
        scored_solutions = []

        for solution in solutions:
            # Zorluk skoru (düşük daha iyi)
            difficulty_level = self._get_difficulty_score(
                solution.get("difficulty", "orta")
            )
            difficulty_score = (5 - difficulty_level) / 5 * 30

            # Karmaşıklık skoru
            complexity_info = next(
                (
                    c
                    for c in complexity_analysis["solutions"]
                    if c["solution_id"] == solution["id"]
                ),
                None,
            )
            complexity_score = 0
            if complexity_info:
                complexity_score = (8 - complexity_info["complexity_score"]) / 8 * 30

            # Süre skoru (kısa daha iyi)
            max_time = max(s["estimated_time_seconds"] for s in solutions)
            time_score = (
                (max_time - solution["estimated_time_seconds"]) / max_time * 20
                if max_time > 0
                else 0
            )

            # Popülerlik skoru
            max_votes = max(s["votes"].get("total", 0) for s in solutions)
            popularity_score = (
                solution["votes"].get("total", 0) / max_votes * 20
                if max_votes > 0
                else 0
            )

            total_score = (
                difficulty_score + complexity_score + time_score + popularity_score
            )

            scored_solutions.append(
                {
                    "solution": solution,
                    "total_score": total_score,
                    "breakdown": {
                        "difficulty_score": difficulty_score,
                        "complexity_score": complexity_score,
                        "time_score": time_score,
                        "popularity_score": popularity_score,
                    },
                }
            )

        # En yüksek skoru bul
        recommended = max(scored_solutions, key=lambda x: x["total_score"])

        return {
            "id": recommended["solution"]["id"],
            "title": recommended["solution"]["title"],
            "score": round(recommended["total_score"], 2),
            "reason": "Çok kriterli değerlendirme sonucu en uygun çözüm",
            "score_breakdown": recommended["breakdown"],
            "why_recommended": self._generate_recommendation_reason(
                recommended["solution"], recommended["breakdown"]
            ),
        }

    def _generate_recommendation_reason(
        self, solution: Dict[str, Any], breakdown: Dict[str, float]
    ) -> str:
        """
        Öneri sebebini açıkla

        Args:
            solution: Çözüm verisi
            breakdown: Skor detayları

        Returns:
            str: Öneri sebebi
        """
        reasons = []

        if breakdown["difficulty_score"] > 20:
            reasons.append(f"kolay anlaşılır ({solution['difficulty']} seviye)")

        if breakdown["complexity_score"] > 20:
            reasons.append("verimli algoritma")

        if breakdown["time_score"] > 15:
            reasons.append(f"hızlı çözüm ({solution['estimated_time_seconds']}s)")

        if breakdown["popularity_score"] > 15:
            reasons.append(f"popüler ({solution['votes'].get('total', 0)} oy)")

        if not reasons:
            return "Dengeli bir çözüm"

        return "Bu çözüm " + ", ".join(reasons) + " özellikleriyle öne çıkıyor."

    async def get_fastest_solution(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        TASK 73.3: En hızlı çözüm önerisi

        Özellikler:
        - Solution time estimation (çözüm süresi tahmini)
        - Efficiency ranking (verimlilik sıralaması)
        - Shortcut identification (kısayol tespiti)

        Args:
            question_id: Soru ID'si

        Returns:
            Dict: Gelişmiş en hızlı çözüm analizi
        """
        try:
            solutions = await self.get_solutions(question_id)

            if not solutions:
                return None

            # TASK 73.3.1: Solution time estimation
            time_estimations = self._estimate_solution_times(solutions)

            # TASK 73.3.2: Efficiency ranking
            efficiency_ranking = self._rank_by_efficiency(solutions, time_estimations)

            # TASK 73.3.3: Shortcut identification
            shortcuts = self._identify_shortcuts(solutions)

            # En hızlı çözümü bul
            fastest_solution = min(
                solutions, key=lambda x: x.get("estimated_time_seconds", float("inf"))
            )

            # Gelişmiş analiz sonucu
            result = {
                "question_id": question_id,
                "fastest_solution": {
                    "id": fastest_solution.get("id"),
                    "title": fastest_solution.get("title"),
                    "category": fastest_solution.get("category"),
                    "difficulty": fastest_solution.get("difficulty"),
                    "estimated_time_seconds": fastest_solution.get(
                        "estimated_time_seconds"
                    ),
                    "steps": fastest_solution.get("steps", []),
                    "step_count": len(fastest_solution.get("steps", [])),
                    "advantages": fastest_solution.get("advantages", []),
                    "tips": fastest_solution.get("tips", []),
                    "video_url": fastest_solution.get("video_url"),
                },
                "time_estimation": time_estimations.get(fastest_solution.get("id"), {}),
                "efficiency_ranking": efficiency_ranking,
                "shortcuts": shortcuts,
                "comparison_with_others": self._compare_with_other_solutions(
                    fastest_solution, solutions
                ),
                "recommendation": {
                    "why_fastest": self._explain_why_fastest(
                        fastest_solution, solutions
                    ),
                    "time_saved": self._calculate_time_saved(
                        fastest_solution, solutions
                    ),
                    "best_for": self._determine_best_use_case(fastest_solution),
                    "prerequisites": fastest_solution.get("prerequisites", []),
                    "difficulty_warning": self._generate_difficulty_warning(
                        fastest_solution
                    ),
                },
            }

            return result

        except Exception as e:
            logger.error(f"En hızlı çözüm hatası: {str(e)}")
            return None

    def _estimate_solution_times(
        self, solutions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        TASK 73.3.1: Çözüm süresi tahmini (detaylı)

        Her çözüm için:
        - Minimum süre (ideal koşullar)
        - Ortalama süre (normal koşullar)
        - Maksimum süre (zorluk yaşanırsa)
        - Adım bazlı süre dağılımı

        Args:
            solutions: Çözüm listesi

        Returns:
            Dict: Çözüm ID -> Süre tahmini mapping
        """
        estimations = {}

        for solution in solutions:
            base_time = solution.get("estimated_time_seconds", 0)
            step_count = len(solution.get("steps", []))
            difficulty = solution.get("difficulty", "orta")
            category = solution.get("category", "klasik")

            # Zorluk çarpanı
            difficulty_multiplier = {
                "kolay": 0.8,
                "orta": 1.0,
                "zor": 1.3,
            }.get(difficulty, 1.0)

            # Kategori çarpanı
            category_multiplier = {
                "hızlı": 0.7,
                "formül": 0.8,
                "klasik": 1.0,
                "görsel": 1.2,
                "mantıksal": 0.9,
            }.get(category, 1.0)

            # Süre tahminleri
            min_time = int(base_time * 0.7 * category_multiplier)
            avg_time = int(base_time * difficulty_multiplier * category_multiplier)
            max_time = int(
                base_time * 1.5 * difficulty_multiplier * category_multiplier
            )

            # Adım bazlı süre dağılımı
            time_per_step = avg_time / step_count if step_count > 0 else 0
            step_times = []

            for idx, step in enumerate(solution.get("steps", []), 1):
                # İlk ve son adımlar genellikle daha hızlı
                if idx == 1 or idx == step_count:
                    step_time = time_per_step * 0.8
                else:
                    step_time = time_per_step

                step_times.append(
                    {
                        "step_number": idx,
                        "estimated_seconds": round(step_time, 1),
                        "description": step.get("description", "")[:50] + "...",
                    }
                )

            estimations[solution.get("id")] = {
                "minimum_time_seconds": min_time,
                "average_time_seconds": avg_time,
                "maximum_time_seconds": max_time,
                "confidence_level": self._calculate_confidence_level(solution),
                "time_per_step": round(time_per_step, 1),
                "step_breakdown": step_times,
                "factors": {
                    "difficulty_impact": f"{(difficulty_multiplier - 1) * 100:+.0f}%",
                    "category_impact": f"{(category_multiplier - 1) * 100:+.0f}%",
                    "step_count_impact": "normal" if step_count <= 10 else "yüksek",
                },
            }

        return estimations

    def _rank_by_efficiency(
        self,
        solutions: List[Dict[str, Any]],
        time_estimations: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        TASK 73.3.2: Verimlilik sıralaması

        Verimlilik kriterleri:
        - Süre (40%)
        - Adım sayısı (20%)
        - Zorluk seviyesi (20%)
        - Başarı oranı/popülerlik (20%)

        Args:
            solutions: Çözüm listesi
            time_estimations: Süre tahminleri

        Returns:
            List[Dict]: Verimlilik sıralaması
        """
        ranked_solutions = []

        # Normalizasyon için min/max değerler
        times = [s.get("estimated_time_seconds", 0) for s in solutions]
        steps = [len(s.get("steps", [])) for s in solutions]
        votes = [s.get("votes", {}).get("total", 0) for s in solutions]

        min_time, max_time = min(times), max(times)
        min_steps, max_steps = min(steps), max(steps)
        min_votes, max_votes = min(votes), max(votes)

        for solution in solutions:
            solution_id = solution.get("id")
            time_est = time_estimations.get(solution_id, {})

            # Süre skoru (düşük daha iyi) - 40%
            time = solution.get("estimated_time_seconds", 0)
            time_score = 0
            if max_time > min_time:
                time_score = (1 - (time - min_time) / (max_time - min_time)) * 40

            # Adım sayısı skoru (az daha iyi) - 20%
            step_count = len(solution.get("steps", []))
            step_score = 0
            if max_steps > min_steps:
                step_score = (
                    1 - (step_count - min_steps) / (max_steps - min_steps)
                ) * 20

            # Zorluk skoru (kolay daha iyi) - 20%
            difficulty_level = self._get_difficulty_score(
                solution.get("difficulty", "orta")
            )
            difficulty_score = (5 - difficulty_level) / 5 * 20

            # Popülerlik skoru (yüksek daha iyi) - 20%
            vote_count = solution.get("votes", {}).get("total", 0)
            popularity_score = 0
            if max_votes > min_votes:
                popularity_score = (
                    (vote_count - min_votes) / (max_votes - min_votes) * 20
                )

            # Toplam verimlilik skoru
            efficiency_score = (
                time_score + step_score + difficulty_score + popularity_score
            )

            ranked_solutions.append(
                {
                    "solution_id": solution_id,
                    "title": solution.get("title"),
                    "efficiency_score": round(efficiency_score, 2),
                    "rank": 0,  # Sıralama sonrası atanacak
                    "score_breakdown": {
                        "time_score": round(time_score, 2),
                        "step_score": round(step_score, 2),
                        "difficulty_score": round(difficulty_score, 2),
                        "popularity_score": round(popularity_score, 2),
                    },
                    "metrics": {
                        "time_seconds": time,
                        "step_count": step_count,
                        "difficulty": solution.get("difficulty"),
                        "votes": vote_count,
                    },
                    "efficiency_rating": self._get_efficiency_rating(efficiency_score),
                }
            )

        # Sırala ve rank ata
        ranked_solutions.sort(key=lambda x: x["efficiency_score"], reverse=True)
        for idx, sol in enumerate(ranked_solutions, 1):
            sol["rank"] = idx

        return ranked_solutions

    def _identify_shortcuts(self, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        TASK 73.3.3: Kısayol tespiti

        Kısayol türleri:
        - Formül kısayolları (direkt formül kullanımı)
        - Mantıksal kısayolları (akıl yürütme ile adım atlama)
        - Görsel kısayollar (geometrik özelliklerden yararlanma)
        - Hesaplama kısayolları (zihinden işlem)

        Args:
            solutions: Çözüm listesi

        Returns:
            Dict: Tespit edilen kısayollar
        """
        shortcuts = {
            "total_shortcuts_found": 0,
            "by_type": {
                "formül": [],
                "mantıksal": [],
                "görsel": [],
                "hesaplama": [],
            },
            "fastest_shortcut": None,
            "easiest_shortcut": None,
            "recommendations": [],
        }

        for solution in solutions:
            solution_shortcuts = []

            # Kategori bazlı kısayol tespiti
            category = solution.get("category", "")

            if category == "formül":
                shortcut = {
                    "solution_id": solution.get("id"),
                    "title": solution.get("title"),
                    "type": "formül",
                    "description": "Direkt formül kullanarak hızlı çözüm",
                    "time_saved_seconds": self._estimate_time_saved(
                        solution, solutions
                    ),
                    "difficulty": solution.get("difficulty"),
                    "steps_skipped": self._estimate_steps_skipped(solution, solutions),
                }
                shortcuts["by_type"]["formül"].append(shortcut)
                solution_shortcuts.append(shortcut)

            elif category == "mantıksal":
                shortcut = {
                    "solution_id": solution.get("id"),
                    "title": solution.get("title"),
                    "type": "mantıksal",
                    "description": "Mantıksal çıkarım ile adım atlama",
                    "time_saved_seconds": self._estimate_time_saved(
                        solution, solutions
                    ),
                    "difficulty": solution.get("difficulty"),
                    "steps_skipped": self._estimate_steps_skipped(solution, solutions),
                }
                shortcuts["by_type"]["mantıksal"].append(shortcut)
                solution_shortcuts.append(shortcut)

            elif category == "görsel":
                shortcut = {
                    "solution_id": solution.get("id"),
                    "title": solution.get("title"),
                    "type": "görsel",
                    "description": "Geometrik özelliklerden yararlanma",
                    "time_saved_seconds": self._estimate_time_saved(
                        solution, solutions
                    ),
                    "difficulty": solution.get("difficulty"),
                    "steps_skipped": self._estimate_steps_skipped(solution, solutions),
                }
                shortcuts["by_type"]["görsel"].append(shortcut)
                solution_shortcuts.append(shortcut)

            elif category == "hızlı":
                shortcut = {
                    "solution_id": solution.get("id"),
                    "title": solution.get("title"),
                    "type": "hesaplama",
                    "description": "Hızlı hesaplama teknikleri",
                    "time_saved_seconds": self._estimate_time_saved(
                        solution, solutions
                    ),
                    "difficulty": solution.get("difficulty"),
                    "steps_skipped": self._estimate_steps_skipped(solution, solutions),
                }
                shortcuts["by_type"]["hesaplama"].append(shortcut)
                solution_shortcuts.append(shortcut)

            # Adım bazlı kısayol tespiti
            steps = solution.get("steps", [])
            for step in steps:
                description = step.get("description", "").lower()

                # Anahtar kelimeler
                if any(
                    keyword in description
                    for keyword in ["formül", "formula", "direkt"]
                ):
                    if not any(s["type"] == "formül" for s in solution_shortcuts):
                        shortcut = {
                            "solution_id": solution.get("id"),
                            "title": solution.get("title"),
                            "type": "formül",
                            "description": f"Adım {step.get('step_number', '?')}: {description[:50]}...",
                            "time_saved_seconds": 10,
                            "difficulty": solution.get("difficulty"),
                            "steps_skipped": 1,
                        }
                        shortcuts["by_type"]["formül"].append(shortcut)
                        solution_shortcuts.append(shortcut)

        # Toplam kısayol sayısı
        shortcuts["total_shortcuts_found"] = sum(
            len(shortcuts_list) for shortcuts_list in shortcuts["by_type"].values()
        )

        # En hızlı kısayol
        all_shortcuts = []
        for shortcuts_list in shortcuts["by_type"].values():
            all_shortcuts.extend(shortcuts_list)

        if all_shortcuts:
            shortcuts["fastest_shortcut"] = max(
                all_shortcuts, key=lambda x: x["time_saved_seconds"]
            )

            shortcuts["easiest_shortcut"] = min(
                all_shortcuts, key=lambda x: self._get_difficulty_score(x["difficulty"])
            )

        # Öneriler
        shortcuts["recommendations"] = self._generate_shortcut_recommendations(
            shortcuts
        )

        return shortcuts

    def _calculate_confidence_level(self, solution: Dict[str, Any]) -> str:
        """
        Süre tahmininin güven seviyesini hesapla

        Args:
            solution: Çözüm verisi

        Returns:
            str: Güven seviyesi (yüksek, orta, düşük)
        """
        usage_count = solution.get("usage_count", 0)
        votes_total = solution.get("votes", {}).get("total", 0)

        # Kullanım ve oy sayısına göre güven
        if usage_count > 50 and votes_total > 10:
            return "yüksek"
        elif usage_count > 10 and votes_total > 3:
            return "orta"
        else:
            return "düşük"

    def _get_efficiency_rating(self, score: float) -> str:
        """
        Verimlilik skorunu derecelendirme

        Args:
            score: Verimlilik skoru (0-100)

        Returns:
            str: Derecelendirme
        """
        if score >= 80:
            return "Mükemmel"
        elif score >= 60:
            return "Çok İyi"
        elif score >= 40:
            return "İyi"
        elif score >= 20:
            return "Orta"
        else:
            return "Düşük"

    def _estimate_time_saved(
        self, solution: Dict[str, Any], all_solutions: List[Dict[str, Any]]
    ) -> int:
        """
        Bu çözümün diğerlerine göre kazandırdığı süreyi tahmin et

        Args:
            solution: Değerlendirilen çözüm
            all_solutions: Tüm çözümler

        Returns:
            int: Kazanılan süre (saniye)
        """
        if not all_solutions:
            return 0

        solution_time = solution.get("estimated_time_seconds", 0)
        avg_time = sum(s.get("estimated_time_seconds", 0) for s in all_solutions) / len(
            all_solutions
        )

        time_saved = int(avg_time - solution_time)
        return max(0, time_saved)

    def _estimate_steps_skipped(
        self, solution: Dict[str, Any], all_solutions: List[Dict[str, Any]]
    ) -> int:
        """
        Bu çözümün atladığı adım sayısını tahmin et

        Args:
            solution: Değerlendirilen çözüm
            all_solutions: Tüm çözümler

        Returns:
            int: Atlanan adım sayısı
        """
        if not all_solutions:
            return 0

        solution_steps = len(solution.get("steps", []))
        avg_steps = sum(len(s.get("steps", [])) for s in all_solutions) / len(
            all_solutions
        )

        steps_skipped = int(avg_steps - solution_steps)
        return max(0, steps_skipped)

    def _generate_shortcut_recommendations(
        self, shortcuts: Dict[str, Any]
    ) -> List[str]:
        """
        Kısayol kullanımı için öneriler oluştur

        Args:
            shortcuts: Kısayol verileri

        Returns:
            List[str]: Öneri listesi
        """
        recommendations = []

        if shortcuts["by_type"]["formül"]:
            recommendations.append(
                "Formül kısayolları sınav için idealdir - ezberleyerek zaman kazanın"
            )

        if shortcuts["by_type"]["mantıksal"]:
            recommendations.append(
                "Mantıksal kısayollar problem çözme becerinizi geliştirir"
            )

        if shortcuts["by_type"]["görsel"]:
            recommendations.append(
                "Görsel kısayollar geometri sorularında çok etkilidir"
            )

        if shortcuts["by_type"]["hesaplama"]:
            recommendations.append(
                "Hızlı hesaplama teknikleri pratikle gelişir - düzenli çalışın"
            )

        if shortcuts["total_shortcuts_found"] == 0:
            recommendations.append("Bu soru için henüz kısayol çözümü eklenmemiş")

        return recommendations

    def _compare_with_other_solutions(
        self, fastest: Dict[str, Any], all_solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        En hızlı çözümü diğerleriyle karşılaştır

        Args:
            fastest: En hızlı çözüm
            all_solutions: Tüm çözümler

        Returns:
            Dict: Karşılaştırma sonuçları
        """
        if len(all_solutions) <= 1:
            return {
                "total_solutions": len(all_solutions),
                "time_advantage": "N/A",
                "step_advantage": "N/A",
                "percentile": 100,
            }

        fastest_time = fastest.get("estimated_time_seconds", 0)
        fastest_steps = len(fastest.get("steps", []))

        # Ortalamalar
        avg_time = sum(s.get("estimated_time_seconds", 0) for s in all_solutions) / len(
            all_solutions
        )
        avg_steps = sum(len(s.get("steps", [])) for s in all_solutions) / len(
            all_solutions
        )

        # Avantajlar
        time_advantage = avg_time - fastest_time
        step_advantage = avg_steps - fastest_steps

        # Yüzdelik dilim
        faster_than = sum(
            1
            for s in all_solutions
            if s.get("estimated_time_seconds", 0) > fastest_time
        )
        percentile = (faster_than / len(all_solutions)) * 100

        return {
            "total_solutions": len(all_solutions),
            "time_advantage_seconds": round(time_advantage, 1),
            "time_advantage_percentage": round(
                (time_advantage / avg_time * 100) if avg_time > 0 else 0, 1
            ),
            "step_advantage": round(step_advantage, 1),
            "percentile": round(percentile, 1),
            "faster_than_count": faster_than,
        }

    def _explain_why_fastest(
        self, fastest: Dict[str, Any], all_solutions: List[Dict[str, Any]]
    ) -> str:
        """
        Neden en hızlı olduğunu açıkla

        Args:
            fastest: En hızlı çözüm
            all_solutions: Tüm çözümler

        Returns:
            str: Açıklama
        """
        reasons = []

        category = fastest.get("category", "")
        if category == "formül":
            reasons.append("direkt formül kullanımı")
        elif category == "hızlı":
            reasons.append("hızlı hesaplama teknikleri")
        elif category == "mantıksal":
            reasons.append("mantıksal kısayollar")

        step_count = len(fastest.get("steps", []))
        if step_count <= 3:
            reasons.append(f"sadece {step_count} adım")

        if len(all_solutions) > 1:
            avg_time = sum(
                s.get("estimated_time_seconds", 0) for s in all_solutions
            ) / len(all_solutions)
            fastest_time = fastest.get("estimated_time_seconds", 0)
            if fastest_time < avg_time * 0.7:
                reasons.append("ortalamadan %30+ daha hızlı")

        if not reasons:
            return "En kısa sürede çözüm sağlar"

        return "Bu çözüm " + ", ".join(reasons) + " sayesinde en hızlı çözümdür."

    def _calculate_time_saved(
        self, fastest: Dict[str, Any], all_solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Kazanılan süreyi hesapla

        Args:
            fastest: En hızlı çözüm
            all_solutions: Tüm çözümler

        Returns:
            Dict: Kazanılan süre bilgileri
        """
        if len(all_solutions) <= 1:
            return {
                "vs_average": 0,
                "vs_slowest": 0,
                "percentage_saved": 0,
            }

        fastest_time = fastest.get("estimated_time_seconds", 0)

        # Ortalama ile karşılaştırma
        avg_time = sum(s.get("estimated_time_seconds", 0) for s in all_solutions) / len(
            all_solutions
        )
        vs_average = avg_time - fastest_time

        # En yavaş ile karşılaştırma
        slowest_time = max(s.get("estimated_time_seconds", 0) for s in all_solutions)
        vs_slowest = slowest_time - fastest_time

        # Yüzde kazanç
        percentage_saved = (vs_average / avg_time * 100) if avg_time > 0 else 0

        return {
            "vs_average_seconds": round(vs_average, 1),
            "vs_slowest_seconds": round(vs_slowest, 1),
            "percentage_saved": round(percentage_saved, 1),
            "time_efficiency": "Mükemmel"
            if percentage_saved > 30
            else "İyi"
            if percentage_saved > 15
            else "Orta",
        }

    def _determine_best_use_case(self, solution: Dict[str, Any]) -> List[str]:
        """
        Bu çözümün en uygun olduğu durumları belirle

        Args:
            solution: Çözüm verisi

        Returns:
            List[str]: Kullanım senaryoları
        """
        use_cases = []

        category = solution.get("category", "")
        difficulty = solution.get("difficulty", "")
        time = solution.get("estimated_time_seconds", 0)

        if time < 60:
            use_cases.append("Sınav sırasında zaman baskısı altında")

        if difficulty == "kolay":
            use_cases.append("Konuya yeni başlayanlar için")

        if category == "formül":
            use_cases.append("Formül ezberleyenler için ideal")

        if category == "hızlı":
            use_cases.append("Hızlı çözüm gereken durumlarda")

        if category == "mantıksal":
            use_cases.append("Problem çözme becerisi geliştirmek için")

        if len(solution.get("steps", [])) <= 3:
            use_cases.append("Basit ve anlaşılır çözüm arayanlar için")

        if not use_cases:
            use_cases.append("Genel kullanım için uygundur")

        return use_cases

    def _generate_difficulty_warning(self, solution: Dict[str, Any]) -> Optional[str]:
        """
        Zorluk uyarısı oluştur

        Args:
            solution: Çözüm verisi

        Returns:
            str: Uyarı mesajı (varsa)
        """
        difficulty = solution.get("difficulty", "")
        category = solution.get("category", "")
        prerequisites = solution.get("prerequisites", [])

        warnings = []

        if difficulty == "zor":
            warnings.append("Bu çözüm ileri seviye bilgi gerektirir")

        if category == "formül" and len(prerequisites) > 2:
            warnings.append("Birden fazla formül bilgisi gereklidir")

        if category == "mantıksal":
            warnings.append("Mantıksal çıkarım yeteneği gerektirir")

        if len(prerequisites) > 3:
            warnings.append(
                f"{len(prerequisites)} ön gereksinim var - önce bunları öğrenin"
            )

        return " | ".join(warnings) if warnings else None

    # ========================================================================
    # Oylama ve İstatistikler
    # ========================================================================

    async def vote_solution(
        self,
        question_id: str,
        solution_id: str,
        user_id: str,
        vote_type: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Çözüme oy ver

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si
            user_id: Kullanıcı ID'si
            vote_type: Oy tipi (upvote, downvote)
            comment: Yorum

        Returns:
            Dict: İşlem sonucu
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return {"success": False, "message": "Soru bulunamadı"}

            # Çözümleri al
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Çözümü bul
            voted = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    # Oy verilerini al
                    votes = solution.get("votes", {"upvotes": 0, "downvotes": 0})

                    # Oy ekle
                    if vote_type == "upvote":
                        votes["upvotes"] = votes.get("upvotes", 0) + 1
                    elif vote_type == "downvote":
                        votes["downvotes"] = votes.get("downvotes", 0) + 1

                    votes["total"] = votes.get("upvotes", 0) - votes.get("downvotes", 0)

                    solution["votes"] = votes

                    # Oy geçmişini kaydet
                    if "vote_history" not in solution:
                        solution["vote_history"] = []

                    solution["vote_history"].append(
                        {
                            "user_id": user_id,
                            "vote_type": vote_type,
                            "comment": comment,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    voted = True
                    break

            if not voted:
                return {"success": False, "message": "Çözüm bulunamadı"}

            # Veritabanını güncelle
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Oy verildi: {solution_id} ({vote_type})")

            return {
                "success": True,
                "total_votes": votes["total"],
                "message": "Oy başarıyla kaydedildi",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Oylama hatası: {str(e)}")
            return {"success": False, "message": str(e)}

    async def get_statistics(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Çözüm istatistiklerini getir

        Args:
            question_id: Soru ID'si

        Returns:
            Dict: İstatistikler
        """
        try:
            solutions = await self.get_solutions(question_id)

            if not solutions:
                return None

            # İstatistikleri hesapla
            stats = {
                "question_id": question_id,
                "total_solutions": len(solutions),
                "by_category": {},
                "by_difficulty": {},
                "average_time": 0,
                "average_steps": 0,
                "most_popular": None,
                "fastest": None,
            }

            # Kategori dağılımı
            for solution in solutions:
                category = solution.get("category", "unknown")
                stats["by_category"][category] = (
                    stats["by_category"].get(category, 0) + 1
                )

            # Zorluk dağılımı
            for solution in solutions:
                difficulty = solution.get("difficulty", "unknown")
                stats["by_difficulty"][difficulty] = (
                    stats["by_difficulty"].get(difficulty, 0) + 1
                )

            # Ortalama süre
            if solutions:
                total_time = sum(s.get("estimated_time_seconds", 0) for s in solutions)
                stats["average_time"] = total_time / len(solutions)

            # Ortalama adım sayısı
            if solutions:
                total_steps = sum(len(s.get("steps", [])) for s in solutions)
                stats["average_steps"] = total_steps / len(solutions)

            # En popüler
            if solutions:
                most_popular = max(
                    solutions, key=lambda x: x.get("votes", {}).get("total", 0)
                )
                stats["most_popular"] = {
                    "id": most_popular.get("id"),
                    "title": most_popular.get("title"),
                    "votes": most_popular.get("votes", {}).get("total", 0),
                }

            # En hızlı
            if solutions:
                fastest = min(
                    solutions,
                    key=lambda x: x.get("estimated_time_seconds", float("inf")),
                )
                stats["fastest"] = {
                    "id": fastest.get("id"),
                    "title": fastest.get("title"),
                    "time": fastest.get("estimated_time_seconds"),
                }

            return stats

        except Exception as e:
            logger.error(f"İstatistik hatası: {str(e)}")
            return None

    # ========================================================================
    # Yardımcı Fonksiyonlar
    # ========================================================================

    def _sort_solutions(
        self, solutions: List[Dict[str, Any]], sort_by: str
    ) -> List[Dict[str, Any]]:
        """
        Çözümleri sırala

        Args:
            solutions: Çözüm listesi
            sort_by: Sıralama kriteri

        Returns:
            List[Dict]: Sıralanmış çözümler
        """
        if sort_by == "difficulty":
            return sorted(
                solutions,
                key=lambda x: self._get_difficulty_score(x.get("difficulty")),
            )
        elif sort_by == "time":
            return sorted(
                solutions, key=lambda x: x.get("estimated_time_seconds", float("inf"))
            )
        elif sort_by == "votes":
            return sorted(
                solutions,
                key=lambda x: x.get("votes", {}).get("total", 0),
                reverse=True,
            )
        elif sort_by == "created_at":
            return sorted(
                solutions, key=lambda x: x.get("created_at", ""), reverse=True
            )
        else:
            return solutions

    def _get_difficulty_score(self, difficulty: str) -> int:
        """
        Zorluk seviyesini sayısal skora çevir

        Args:
            difficulty: Zorluk seviyesi

        Returns:
            int: Zorluk skoru (1-5)
        """
        difficulty_map = {
            "çok kolay": 1,
            "very_easy": 1,
            "kolay": 2,
            "easy": 2,
            "orta": 3,
            "medium": 3,
            "zor": 4,
            "hard": 4,
            "çok zor": 5,
            "very_hard": 5,
        }
        return difficulty_map.get(difficulty.lower() if difficulty else "", 3)

    # ========================================================================
    # TASK 73.4: Öğrenci Çözüm Paylaşımı
    # ========================================================================

    async def get_student_submissions(
        self,
        question_id: str,
        sort_by: str = "votes",
        min_votes: int = 0,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        TASK 73.4: Öğrenci tarafından gönderilen çözümleri getir

        Özellikler:
        - User-submitted solutions (öğrenci çözümleri)
        - Peer review system entegrasyonu
        - Upvote/downvote mekanizması ile sıralama

        Args:
            question_id: Soru ID'si
            sort_by: Sıralama kriteri (votes, created_at, difficulty)
            min_votes: Minimum oy sayısı filtresi

        Returns:
            List[Dict]: Öğrenci çözümleri
        """
        try:
            # Tüm çözümleri getir
            solutions = await self.get_solutions(question_id)

            if solutions is None:
                return None

            # Sadece öğrenci çözümlerini filtrele
            student_solutions = [
                s for s in solutions if s.get("created_by_type") == "student"
            ]

            # Minimum oy filtresi
            if min_votes > 0:
                student_solutions = [
                    s
                    for s in student_solutions
                    if s.get("votes", {}).get("total", 0) >= min_votes
                ]

            # Sıralama
            if sort_by == "votes":
                student_solutions.sort(
                    key=lambda x: x.get("votes", {}).get("total", 0), reverse=True
                )
            elif sort_by == "created_at":
                student_solutions.sort(
                    key=lambda x: x.get("created_at", ""), reverse=True
                )
            elif sort_by == "difficulty":
                student_solutions.sort(
                    key=lambda x: self._get_difficulty_score(
                        x.get("difficulty", "orta")
                    )
                )

            # Her çözüm için peer review bilgilerini ekle
            for solution in student_solutions:
                solution["peer_review_summary"] = self._get_peer_review_summary(
                    solution
                )

            return student_solutions

        except Exception as e:
            logger.error(f"Öğrenci çözümleri getirme hatası: {str(e)}")
            return []

    async def get_solution_reviews(
        self, question_id: str, solution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        TASK 73.4: Çözümün peer review'larını getir

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si

        Returns:
            Dict: Review bilgileri
        """
        try:
            solution = await self.get_solution_by_id(question_id, solution_id)

            if not solution:
                return None

            votes = solution.get("votes", {})
            vote_history = solution.get("vote_history", [])

            # Review istatistikleri
            reviews = {
                "solution_id": solution_id,
                "total_reviews": len(vote_history),
                "vote_summary": {
                    "upvotes": votes.get("upvotes", 0),
                    "downvotes": votes.get("downvotes", 0),
                    "total_score": votes.get("total", 0),
                    "approval_rate": self._calculate_approval_rate(votes),
                },
                "reviews": [],
                "statistics": {
                    "average_rating": self._calculate_average_rating(votes),
                    "review_distribution": self._get_review_distribution(vote_history),
                    "most_helpful_comments": self._get_most_helpful_comments(
                        vote_history
                    ),
                },
            }

            # Review detayları (yorumları gizle - sadece istatistik)
            for review in vote_history:
                reviews["reviews"].append(
                    {
                        "vote_type": review.get("vote_type"),
                        "has_comment": bool(review.get("comment")),
                        "comment_preview": review.get("comment", "")[:50] + "..."
                        if review.get("comment")
                        else None,
                        "timestamp": review.get("timestamp"),
                    }
                )

            return reviews

        except Exception as e:
            logger.error(f"Review getirme hatası: {str(e)}")
            return None

    async def get_top_rated_solutions(
        self,
        question_id: str,
        limit: int = 5,
        created_by_type: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        TASK 73.4: En çok oy alan çözümleri getir

        Args:
            question_id: Soru ID'si
            limit: Maksimum sonuç sayısı
            created_by_type: Oluşturan tipi filtresi (student, teacher, ai)

        Returns:
            List[Dict]: En iyi çözümler
        """
        try:
            solutions = await self.get_solutions(question_id)

            if solutions is None:
                return None

            # Oluşturan tipi filtresi
            if created_by_type:
                solutions = [
                    s for s in solutions if s.get("created_by_type") == created_by_type
                ]

            # Oy sayısına göre sırala
            solutions.sort(
                key=lambda x: x.get("votes", {}).get("total", 0), reverse=True
            )

            # Limit uygula
            top_solutions = solutions[:limit]

            # Her çözüm için ek bilgiler
            for solution in top_solutions:
                solution["ranking_info"] = {
                    "total_votes": solution.get("votes", {}).get("total", 0),
                    "approval_rate": self._calculate_approval_rate(
                        solution.get("votes", {})
                    ),
                    "review_count": len(solution.get("vote_history", [])),
                    "created_by_type": solution.get("created_by_type"),
                }

            return top_solutions

        except Exception as e:
            logger.error(f"Top rated çözümler hatası: {str(e)}")
            return []

    async def remove_vote(
        self, question_id: str, solution_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        TASK 73.4: Verilen oyu geri çek

        Args:
            question_id: Soru ID'si
            solution_id: Çözüm ID'si
            user_id: Kullanıcı ID'si

        Returns:
            Dict: İşlem sonucu
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return {"success": False, "message": "Soru bulunamadı"}

            # Çözümleri al
            solutions_data = question.alternative_solutions or {}
            solutions = solutions_data.get("solutions", [])

            # Çözümü bul ve oyu geri çek
            vote_removed = False
            for solution in solutions:
                if solution.get("id") == solution_id:
                    vote_history = solution.get("vote_history", [])

                    # Kullanıcının oyunu bul
                    user_vote = None
                    for idx, vote in enumerate(vote_history):
                        if vote.get("user_id") == user_id:
                            user_vote = vote
                            vote_history.pop(idx)
                            break

                    if user_vote:
                        # Oy sayılarını güncelle
                        votes = solution.get("votes", {})
                        vote_type = user_vote.get("vote_type")

                        if vote_type == "upvote":
                            votes["upvotes"] = max(0, votes.get("upvotes", 0) - 1)
                        elif vote_type == "downvote":
                            votes["downvotes"] = max(0, votes.get("downvotes", 0) - 1)

                        votes["total"] = votes.get("upvotes", 0) - votes.get(
                            "downvotes", 0
                        )

                        solution["votes"] = votes
                        solution["vote_history"] = vote_history
                        vote_removed = True

                    break

            if not vote_removed:
                return {"success": False, "message": "Oy bulunamadı"}

            # Veritabanını güncelle
            solutions_data["solutions"] = solutions
            question.alternative_solutions = solutions_data
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Oy geri çekildi: {solution_id} (user: {user_id})")

            return {
                "success": True,
                "total_votes": votes["total"],
                "message": "Oy başarıyla geri çekildi",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Oy geri çekme hatası: {str(e)}")
            return {"success": False, "message": str(e)}

    # ========================================================================
    # Yardımcı Metodlar (TASK 73.4)
    # ========================================================================

    def _get_peer_review_summary(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Peer review özeti oluştur

        Args:
            solution: Çözüm verisi

        Returns:
            Dict: Review özeti
        """
        votes = solution.get("votes", {})
        vote_history = solution.get("vote_history", [])

        return {
            "total_reviews": len(vote_history),
            "upvotes": votes.get("upvotes", 0),
            "downvotes": votes.get("downvotes", 0),
            "net_score": votes.get("total", 0),
            "approval_rate": self._calculate_approval_rate(votes),
            "has_comments": any(v.get("comment") for v in vote_history),
            "comment_count": sum(1 for v in vote_history if v.get("comment")),
        }

    def _calculate_approval_rate(self, votes: Dict[str, int]) -> float:
        """
        Onay oranını hesapla

        Args:
            votes: Oy verileri

        Returns:
            float: Onay oranı (0-100)
        """
        upvotes = votes.get("upvotes", 0)
        downvotes = votes.get("downvotes", 0)
        total = upvotes + downvotes

        if total == 0:
            return 0.0

        return round((upvotes / total) * 100, 1)

    def _calculate_average_rating(self, votes: Dict[str, int]) -> float:
        """
        Ortalama rating hesapla (5 üzerinden)

        Args:
            votes: Oy verileri

        Returns:
            float: Ortalama rating
        """
        approval_rate = self._calculate_approval_rate(votes)
        # 0-100 aralığını 0-5 aralığına dönüştür
        return round((approval_rate / 100) * 5, 1)

    def _get_review_distribution(
        self, vote_history: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Review dağılımını hesapla

        Args:
            vote_history: Oy geçmişi

        Returns:
            Dict: Dağılım bilgisi
        """
        distribution = {
            "upvotes": 0,
            "downvotes": 0,
            "with_comments": 0,
            "without_comments": 0,
        }

        for vote in vote_history:
            vote_type = vote.get("vote_type")
            has_comment = bool(vote.get("comment"))

            if vote_type == "upvote":
                distribution["upvotes"] += 1
            elif vote_type == "downvote":
                distribution["downvotes"] += 1

            if has_comment:
                distribution["with_comments"] += 1
            else:
                distribution["without_comments"] += 1

        return distribution

    def _get_most_helpful_comments(
        self, vote_history: List[Dict[str, Any]]
    ) -> List[str]:
        """
        En yararlı yorumları getir (upvote ile birlikte olanlar)

        Args:
            vote_history: Oy geçmişi

        Returns:
            List[str]: Yorum listesi
        """
        helpful_comments = []

        for vote in vote_history:
            if vote.get("vote_type") == "upvote" and vote.get("comment"):
                comment = vote.get("comment", "")
                if len(comment) > 10:  # Anlamlı yorumlar
                    helpful_comments.append(comment[:100])  # İlk 100 karakter

        return helpful_comments[:5]  # En fazla 5 yorum
