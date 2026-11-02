"""
电影提示词生成器（第二版优化）
- 强化时长控制：总时长、片段时长均可任意配置，自动计算片段数
- 新增全局风格要求：确保所有生成内容在视觉、情绪、节奏上高度统一
- 提示词模板进一步结构化，避免指令模糊
"""

from typing import List, Dict
import logging

# 您的依赖
from ros.common.imports import *
from src.util import *

logger = logging.getLogger(__name__)


class MoviePromptGeneratorV2:
    def __init__(
        self,
        global_style: str = "",              # 全片统一风格要求（如“水墨武侠，冷色调”）
        total_duration: int = 20,            # 电影总时长（秒）
        clip_duration: int = 5,              # 每个视频片段时长（秒）
        image_model: str = "Stable Diffusion",
        video_model: str = "VideoGen",
    ):
        self.global_style = global_style
        self.total_duration = total_duration
        self.clip_duration = clip_duration
        self.clip_count = total_duration // clip_duration
        if total_duration % clip_duration != 0:
            logger.warning(f"总时长{total_duration}秒不能被{clip_duration}整除，将按{self.clip_count}个片段处理")
        self.image_model = image_model
        self.video_model = video_model

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        try:
            return getResult(messages)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    # ---------- 提示词模板（全部注入 global_style） ----------
    def _base_context(self) -> str:
        """生成全局风格约束文本，所有模板复用"""
        if self.global_style:
            return f"【全片统一风格要求】{self.global_style}\n"
        return ""

    def story_framework_prompt(self, requirement: str) -> str:
        base = self._base_context()
        return (
            f"{base}"
            f"【任务】根据电影需求，设计一个 {self.total_duration} 秒的电影故事框架。\n"
            f"【需求】{requirement}\n"
            f"【要求】1. 框架需包含精确到秒的时间分配，每{self.clip_duration}秒一个段落；"
            f"2. 每个段落描述核心画面、关键动作与情绪；"
            f"3. 结尾必须留下悬念；"
            f"4. 严格遵循全片统一风格要求；"
            f"5. 只输出框架文本，不要解释。"
        )

    def opening_image_prompt(self, story_framework: str) -> str:
        base = self._base_context()
        return (
            f"{base}"
            f"【任务】为以下故事框架的第0秒画面生成图像提示词。\n"
            f"【故事框架】{story_framework}\n"
            f"【要求】1. 详细描述场景、光线、构图、风格，必须符合全片统一风格；"
            f"2. 输出纯英文提示词，适合{self.image_model}；"
            f"3. 不要包含任何解释。"
        )

    def first_clip_video_prompt(self, story_framework: str, opening_img_prompt: str, clip_index: int) -> str:
        base = self._base_context()
        start_t = clip_index * self.clip_duration
        end_t = start_t + self.clip_duration
        return (
            f"{base}"
            f"【任务】为电影片段 {start_t}-{end_t} 秒生成视频提示词。\n"
            f"【完整故事框架】{story_framework}\n"
            f"【该片段起始画面】{opening_img_prompt}\n"
            f"【要求】1. 描述这{self.clip_duration}秒内的连续动作、镜头运动和转场，保持风格统一；"
            f"2. 提示词适合{self.video_model}；"
            f"3. 只输出提示词，不要解释。"
        )

    def next_clip_video_prompt(self, story_framework: str, previous_clips: List[str], clip_index: int) -> str:
        base = self._base_context()
        start_t = clip_index * self.clip_duration
        end_t = start_t + self.clip_duration
        prev_str = "\n".join(
            [f"片段{i*self.clip_duration}-{(i+1)*self.clip_duration}秒提示词：{p}" for i, p in enumerate(previous_clips)]
        )
        return (
            f"{base}"
            f"【任务】为电影片段 {start_t}-{end_t} 秒生成视频提示词。\n"
            f"【完整故事框架】{story_framework}\n"
            f"【已生成的前序片段】\n{prev_str}\n"
            f"【要求】1. 描述这{self.clip_duration}秒内动作，与前一片段无缝衔接，整体风格一致；"
            f"2. 适合{self.video_model}；"
            f"3. 直接输出提示词。"
        )

    # ---------- 核心流水线 ----------
    def generate_opening_only(self, requirement: str) -> Dict:
        """快速生成开场画面+首个片段（用于预览风格）"""
        story_prompt = self.story_framework_prompt(requirement)
        story = self._call_llm([{"role": "user", "content": story_prompt}])

        img_prompt = self._call_llm([{"role": "user", "content": self.opening_image_prompt(story)}])
        video_prompt = self._call_llm([
            {"role": "user", "content": self.first_clip_video_prompt(story, img_prompt, 0)}
        ])
        return {
            "story_framework": story,
            "image_prompt": img_prompt,
            "first_clip_video_prompt": video_prompt
        }

    def generate_full_movie(self, requirement: str) -> Dict:
        """完整流程：框架 → 图像 → 所有视频片段"""
        story_prompt = self.story_framework_prompt(requirement)
        story = self._call_llm([{"role": "user", "content": story_prompt}])

        img_prompt = self._call_llm([{"role": "user", "content": self.opening_image_prompt(story)}])

        video_prompts = []
        for i in range(self.clip_count):
            if i == 0:
                prompt_text = self.first_clip_video_prompt(story, img_prompt, i)
            else:
                prompt_text = self.next_clip_video_prompt(story, video_prompts, i)
            clip = self._call_llm([{"role": "user", "content": prompt_text}])
            video_prompts.append(clip)
            logger.info(f"生成进度 {i+1}/{self.clip_count}")

        return {
            "global_style": self.global_style,
            "total_duration": self.total_duration,
            "clip_duration": self.clip_duration,
            "story_framework": story,
            "image_prompt": img_prompt,
            "video_prompts": video_prompts,
        }


# ---------- 使用示例 ----------
def run():
    # 示例：时长可自由定制，且加入统一风格要求（武打 + 水墨美学）
    generator = MoviePromptGeneratorV2(
        global_style="中国古代水墨风格，动态泼墨特效，色彩以黑白灰为主，点缀朱砂红，动作凌厉且富有诗意。",
        total_duration=30,   # 30秒电影
        clip_duration=6      # 每6秒一个片段，共5个片段
    )

    result = generator.generate_full_movie("生成一个武打电影，主角在山巅决战")
    print("全局风格：", result["global_style"])
    print("总时长/片段时长：", result["total_duration"], "/", result["clip_duration"])
    print("故事框架：", result["story_framework"])
    print("开场画面提示词：", result["image_prompt"])
    for i, vp in enumerate(result["video_prompts"]):
        print(f"片段{i+1}视频提示词：", vp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()