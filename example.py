import sys
import asyncio
from client import MemoryClient

async def add_messages(conversation_id: str, user_id: str, messages: list):
    mc = MemoryClient()
    for m in messages:
        await mc.add_message(conversation_id, user_id, m["query"], m["answer"])


async def get_memory(query: str, user_id: str):
    mc = MemoryClient()
    resp = await mc.get_memory(query, user_id)
    print(resp)


user_id = "user_1"

async def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            await add_messages("conv_1", user_id, [
                {"query": "今度旅行に行こうと思ってる", "answer": "へえ、どこに？"},
                {"query": "温泉！やっぱ旅行といえば温泉でしょう", "answer": "いいねえ。近場？遠く？"},
                {"query": "箱根かなあ、近いし", "answer": "箱根いいね。遠いと移動で疲れちゃって意味ないもんね"}
            ])
        elif sys.argv[1] == "2":
            await add_messages("conv_2", user_id, [
                {"query": "誕生日の過ごし方考えてる", "answer": "そうなんだ。いつ？"},
                {"query": "7月18日だよ", "answer": "ずいぶん先だね"},
                {"query": "そうなんだけど、20代最後の節目の年だからね", "answer": "なるほど。食事とか特別なものがいいね"},
                {"query": "野菜が好きだからたべたい。キャベツとか", "answer": "キャベツか。肉とかじゃないんだ"}
            ])
        elif sys.argv[1] == "3":
            await add_messages("conv_3", user_id, [
                {"query": "動物園行きたい", "answer": "動物見たいね。何が好き？"},
                {"query": "ネコ科全般。チーターの鳴き声が聞きたい", "answer": "がおーってやつ？"},
                {"query": "ニャンって鳴く", "answer": "そうなの・・・"}
            ])
    else:
        await get_memory("ユーザーの誕生日は？", user_id)

asyncio.run(main())
