from app.adapters.mock_storyteller import MockStoryteller
from app.domain.models import Character, DiceResult, Player, Room, StoryEntry, World


def story_room() -> Room:
    players = [
        Player(
            id="player-1",
            name="小明",
            role="斥候",
            action="沿著燒焦電纜尋找控制室",
            action_approach="insight",
            character=Character(
                name="阿澈",
                background="維修學徒",
                trait="觀察細膩",
                weakness="害怕密閉空間",
                courage=0,
                insight=2,
                bond=1,
            ),
        ),
        Player(
            id="player-2",
            name="小華",
            role="協調者",
            action="說服警衛暫緩封鎖通道",
            action_approach="bond",
            character=Character(
                name="若蘭",
                background="社區志工",
                trait="善於傾聽",
                weakness="過度相信承諾",
                courage=0,
                insight=1,
                bond=2,
            ),
        ),
        Player(
            id="player-3",
            name="小杰",
            role="先鋒",
            action="徒手撐住即將落下的防火門",
            action_approach="courage",
            character=Character(
                name="鐵山",
                background="貨運司機",
                trait="臨危不亂",
                weakness="不肯求援",
                courage=2,
                insight=0,
                bond=1,
            ),
        ),
    ]
    return Room(
        id="story-room",
        room_code="STORY1",
        status="RESOLVING",
        version=4,
        round_number=2,
        world=World(
            name="停電車站",
            story_title="停電車站",
            premise="暴雨讓山城車站斷電，末班列車失去聯絡。",
            objective="在洪水淹入月台前恢復號誌。",
            opening_scene="緊急照明熄滅，廣播只剩規律雜音。",
            core_obstacle="控制室位於已封鎖的舊月台。",
            tone="adventure",
        ),
        max_rounds=4,
        initial_player_count=3,
        progress_points=3,
        danger_points=2,
        players=players,
        entries=[
            StoryEntry(
                id="previous",
                type="narrator",
                title="故事主持人",
                round_number=1,
                text="眾人在積水中找到通往舊月台的維修梯，但遠處傳來防火門啟動聲。",
            )
        ],
        dice_results=[
            DiceResult("player-1", 2, 4, 5, "insight", 2, 11, 11, "SUCCESS", 2, 0),
            DiceResult("player-2", 2, 3, 3, "bond", 2, 8, 8, "PARTIAL_SUCCESS", 1, 1),
            DiceResult("player-3", 2, 1, 2, "courage", 2, 5, 5, "FAILURE", 0, 2),
        ],
    )


def test_mock_round_narrative_causally_combines_scene_characters_actions_dice_and_state_deltas() -> None:
    text = MockStoryteller().resolve_round(story_room())

    assert text == (
        "承接上一幕：眾人在積水中找到通往舊月台的維修梯，但遠處傳來防火門啟動聲。\n"
        "阿澈（觀察細膩；弱點：害怕密閉空間）沿著燒焦電纜尋找控制室；"
        "骰點 4+5+洞察2=11，行動成功，這項行動形成可見突破，讓「在洪水淹入月台前恢復號誌。」向前推進（進度 +2）。\n"
        "若蘭（善於傾聽；弱點：過度相信承諾）說服警衛暫緩封鎖通道；"
        "骰點 3+3+連結2=8，部分成功，這項行動帶來進展，但「過度相信承諾」使新的牽制浮現（進度 +1、危機 +1）。\n"
        "鐵山（臨危不亂；弱點：不肯求援）徒手撐住即將落下的防火門；"
        "骰點 1+2+勇氣2=5，行動失敗，這項行動沒有達成預期並讓眼前阻礙惡化，但仍留下可繼續嘗試的線索（危機 +2）。\n"
        "本回合固定結算為 1 次成功、1 次部分成功與 1 次失敗，共增加進度 3、危機 3；下一幕，團隊必須承接上述突破與牽制，在危機擴大前繼續朝「在洪水淹入月台前恢復號誌。」行動。"
    )


def test_mock_ending_turns_canonical_result_and_cost_into_concrete_consequences() -> None:
    room = story_room()
    room.progress_points = 12
    room.danger_points = 8
    room.ending_result = "PARTIAL_SUCCESS"
    room.ending_cost = "SIGNIFICANT"

    text = MockStoryteller().resolve_ending(room)

    assert text == (
        "承接最後事件：眾人在積水中找到通往舊月台的維修梯，但遠處傳來防火門啟動聲。"
        "團隊只完成「在洪水淹入月台前恢復號誌。」的核心部分，仍有關鍵缺口尚未補上。"
        "這項結果伴隨明確代價：上一幕留下的風險成為必須立刻處理的未解問題。"
        "最終固定狀態為進度 12、危機 8；故事沒有改判規則引擎的部分成功與明確代價。"
    )
