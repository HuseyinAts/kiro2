"""
Dynamic Content Management System
Teknofest 2025 - Separates content from code
"""

import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages educational content from external files"""

    def __init__(self, content_dir: str = "content"):
        self.content_dir = Path(content_dir)
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        self.last_cache_update = {}

        # Ensure content directory exists
        self.content_dir.mkdir(exist_ok=True)

        # Load all content on initialization
        self._load_all_content()

    def _load_all_content(self):
        """Load all YAML/JSON content files"""
        for file_path in self.content_dir.glob("*.yaml"):
            self._load_file(file_path)

        for file_path in self.content_dir.glob("*.json"):
            self._load_file(file_path)

        logger.info(f"Loaded {len(self.cache)} content files")

    def _load_file(self, file_path: Path) -> dict | None:
        """Load a single content file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                if file_path.suffix == ".yaml":
                    content = yaml.safe_load(f)
                else:
                    content = json.load(f)

            key = file_path.stem  # filename without extension
            self.cache[key] = content
            self.last_cache_update[key] = datetime.now()

            logger.debug(f"Loaded content from {file_path}")
            return content

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return None

    def get_content(self, content_key: str, refresh: bool = False) -> dict | None:
        """Get content by key, with optional refresh"""

        # Check if refresh needed
        if refresh or self._should_refresh(content_key):
            file_path = self._find_content_file(content_key)
            if file_path:
                self._load_file(file_path)

        return self.cache.get(content_key)

    def _should_refresh(self, content_key: str) -> bool:
        """Check if content should be refreshed"""
        if content_key not in self.last_cache_update:
            return True

        last_update = self.last_cache_update[content_key]
        return datetime.now() - last_update > self.cache_ttl

    def _find_content_file(self, content_key: str) -> Path | None:
        """Find content file by key"""
        for ext in [".yaml", ".json"]:
            file_path = self.content_dir / f"{content_key}{ext}"
            if file_path.exists():
                return file_path
        return None

    @lru_cache(maxsize=100)
    def get_topic_content(
        self, subject: str, topic_id: str, difficulty: str = "intermediate"
    ) -> str | None:
        """Get specific topic content by subject and topic ID"""

        content = self.get_content(subject)
        if not content:
            return None

        # Navigate the content structure
        topics = content.get("topics", [])
        for topic in topics:
            if topic.get("id") == topic_id:
                return self._format_topic_content(topic, difficulty)

        return None

    def _format_topic_content(self, topic: dict, difficulty: str) -> str:
        """Format topic content for display"""
        lines = []

        # Title and basic info
        lines.append(f"[BOOKS] **{topic.get('title', 'Konu')}**\n")

        # Subtopics
        subtopics = topic.get("subtopics", [])
        for subtopic in subtopics:
            lines.append(f"**{subtopic.get('name', '')}**")
            lines.append(subtopic.get("content", ""))

            # Add examples if available
            examples = subtopic.get("examples", [])
            if examples:
                lines.append("\n[BULB] **Örnekler:**")
                for example in examples:
                    lines.append(f"• {example}")

            # Add difficulty-specific content
            levels = subtopic.get("difficulty_levels", {})
            if difficulty in levels:
                lines.append(f"\n[CHART] **{difficulty.title()} Seviye:**")
                lines.append(levels[difficulty])

            lines.append("")  # Empty line between subtopics

        return "\n".join(lines)

    def get_study_plan(
        self, subject: str, plan_type: str = "intensive_4_weeks"
    ) -> dict | None:
        """Get study plan from content"""

        content = self.get_content(subject)
        if not content:
            return None

        study_plans = content.get("study_plans", {})
        return study_plans.get(plan_type)

    def get_resources(
        self, subject: str, resource_type: str | None = None
    ) -> list[dict]:
        """Get learning resources"""

        content = self.get_content(subject)
        if not content:
            return []

        resources = content.get("resources", {})

        if resource_type:
            return resources.get(resource_type, [])

        # Return all resources flattened
        all_resources = []
        for res_type, res_list in resources.items():
            for resource in res_list:
                resource["type"] = res_type
                all_resources.append(resource)

        return all_resources

    def search_content(self, query: str, subject: str | None = None) -> list[dict]:
        """Search across all content"""
        results = []
        query_lower = query.lower()

        # Search in specific subject or all
        subjects_to_search = [subject] if subject else self.cache.keys()

        for subj in subjects_to_search:
            content = self.get_content(subj)
            if not content:
                continue

            # Search in topics
            topics = content.get("topics", [])
            for topic in topics:
                if self._search_in_dict(topic, query_lower):
                    results.append({"subject": subj, "type": "topic", "data": topic})

        return results

    def _search_in_dict(self, data: Any, query: str) -> bool:
        """Recursively search for query in nested structure"""
        if isinstance(data, str):
            return query in data.lower()
        if isinstance(data, dict):
            for value in data.values():
                if self._search_in_dict(value, query):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._search_in_dict(item, query):
                    return True
        return False

    def get_exam_tips(self, subject: str, tip_type: str = "general") -> list[str]:
        """Get exam tips and strategies"""

        content = self.get_content(subject)
        if not content:
            return []

        tips = content.get("tips", {})
        return tips.get(tip_type, [])

    def update_content(self, content_key: str, new_content: dict) -> bool:
        """Update content and save to file"""
        try:
            # Update cache
            self.cache[content_key] = new_content
            self.last_cache_update[content_key] = datetime.now()

            # Save to file
            file_path = self.content_dir / f"{content_key}.yaml"
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(new_content, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"Updated content: {content_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to update content {content_key}: {e}")
            return False


class ContentProvider:
    """Provides content to agents with proper formatting"""

    def __init__(self):
        self.manager = ContentManager()

    async def get_lgs_math_content(self, topic: str | None = None) -> str:
        """Get LGS mathematics content"""

        if topic:
            content = self.manager.get_topic_content("lgs_matematik", topic)
            if content:
                return content

        # Return general overview
        content = self.manager.get_content("lgs_matematik")
        if not content:
            return "İçerik yüklenemedi. Lütfen daha sonra tekrar deneyin."

        # Format overview
        lines = ["[BOOKS] **LGS MATEMATİK KONULARI**\n"]

        topics = content.get("topics", [])
        for i, topic in enumerate(topics, 1):
            lines.append(f"{i}. **{topic.get('title', 'Konu')}**")

            subtopics = topic.get("subtopics", [])
            for subtopic in subtopics:
                lines.append(f"   • {subtopic.get('name', '')}")
            lines.append("")

        # Add study tips
        tips = self.manager.get_exam_tips("lgs_matematik")
        if tips:
            lines.append("\n[BULB] **Çalışma İpuçları:**")
            for tip in tips[:5]:  # Show first 5 tips
                lines.append(f"[CHECK] {tip}")

        return "\n".join(lines)

    async def get_study_resources(
        self, subject: str, resource_type: str | None = None
    ) -> str:
        """Get formatted study resources"""

        resources = self.manager.get_resources(subject, resource_type)

        if not resources:
            return "Bu konu için kaynak bulunamadı."

        lines = ["📖 **Önerilen Kaynaklar**\n"]

        for resource in resources[:10]:  # Limit to 10 resources
            emoji = {"videos": "🎥", "practice_sets": "[MEMO]", "books": "[BOOKS]"}.get(
                resource.get("type", ""), "📌"
            )

            lines.append(f"{emoji} **{resource.get('title', 'Kaynak')}**")

            if "duration" in resource:
                lines.append(f"   ⏱️ Süre: {resource['duration']} dakika")
            if "author" in resource:
                lines.append(f"   ✍️ Yazar: {resource['author']}")
            if "url" in resource:
                lines.append(f"   [LINK] Link: {resource['url']}")

            lines.append("")

        return "\n".join(lines)

    async def get_personalized_plan(
        self, subject: str, available_hours: int = 20, duration_weeks: int = 4
    ) -> str:
        """Get personalized study plan"""

        # Determine plan type based on duration
        if duration_weeks <= 4:
            plan_type = "intensive_4_weeks"
        else:
            plan_type = "regular_3_months"

        plan = self.manager.get_study_plan(subject, plan_type)

        if not plan:
            return "Çalışma planı oluşturulamadı."

        lines = [f"📅 **{duration_weeks} Haftalık Kişisel Çalışma Planı**\n"]

        # Format the plan based on structure
        for week_or_month, details in plan.items():
            lines.append(f"**{week_or_month.upper()}**")

            if isinstance(details, list):
                for item in details:
                    if "topic" in item:
                        lines.append(f"• Konu: {item['topic']}")
                        lines.append(f"  Süre: {item.get('hours', 0)} saat")
                        lines.append(f"  Odak: {item.get('focus', '')}")
            elif isinstance(details, dict):
                if "topics" in details:
                    lines.append(f"• Konular: {', '.join(details['topics'])}")
                if "weekly_hours" in details:
                    lines.append(f"• Haftalık: {details['weekly_hours']} saat")
                if "practice_tests" in details:
                    lines.append(f"• Deneme: {details['practice_tests']} adet")

            lines.append("")

        # Add personalized recommendations based on available hours
        lines.append("\n[TARGET] **Kişisel Öneriler:**")
        daily_hours = available_hours / 7
        if daily_hours < 2:
            lines.append("• Günde en az 2 saat ayırmaya çalışın")
        elif daily_hours > 4:
            lines.append("• Yoğun program - düzenli molalar verin")
        else:
            lines.append("• İdeal çalışma süresi!")

        return "\n".join(lines)


# Example usage
async def example_usage():
    """Example of using content management system"""

    provider = ContentProvider()

    # Get LGS math content
    math_content = await provider.get_lgs_math_content()
    print(math_content)

    # Get specific topic
    topic_content = await provider.get_lgs_math_content("sayilar_islemler")
    print(topic_content)

    # Get resources
    resources = await provider.get_study_resources("lgs_matematik", "videos")
    print(resources)

    # Get personalized plan
    plan = await provider.get_personalized_plan("lgs_matematik", available_hours=20)
    print(plan)


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
