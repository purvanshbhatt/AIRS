import pytest
from app.schemas.board_story import BoardStory, BoardStorySection

def test_board_story_schema_validation():
    # Needs exactly 10 sections
    sections = [
        BoardStorySection(section_id="s1", title="S1", content="...")
    ]
    with pytest.raises(ValueError):
        BoardStory(sections=sections)
        
    sections_10 = [
        BoardStorySection(section_id=str(i), title=str(i), content="...")
        for i in range(10)
    ]
    story = BoardStory(sections=sections_10)
    assert len(story.sections) == 10
