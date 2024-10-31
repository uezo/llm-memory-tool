# 🎃 llm-memory-tool 👻

An experimental implementation for long-term memory in LLMs through function calling.
Helping your AI remember with a sprinkle of magic! 🪄✨


## 🎃 Setup

1. Clone this repository to your computer.

1. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

1. Start the server:

    ```sh
    export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    uvicorn server:app
    ```

    Go to http://localhost:8000/docs to verify that the server has started successfully.


## 👻 Usage

Send a user request and AI response to `POST /messages` to update the memory records.
To retrieve the stored memories, register `GET /summaries` as a function tool for your AI Agent.


You can try the example steps below:


1. Run the example to add the first conversation messages:

    ```sh
    python example.py 1
    ```

1. Run the example to get memory. At this point, no memories will be retrieved, as the first conversation is still ongoing:

    ```sh
    python example.py
    {'detail': 'No records found for the given user_id and query'}
    ```

1. Run the example to add the second conversation messages:

    ```sh
    python example.py 2
    ```

1. Run the example to get memory again. This time, the summary of the first conversation appears:

    ```sh
    python example.py
    {'results': [{'conversation_id': 'conv_1', 'user_id': 'user_1', 'created_at': '2024-10-31T11:57:32.333432', 'summary': 'ユーザーは旅行を計画しており、温泉を目的地に選ぶと話しています。AIはその選択に賛同し、近場の箱根を提案したユーザーに共感し、移動の疲れを避けることの重要性を述べました。キーワード: 温泉、旅行、箱根、移動。'}]}
    ```

1. Run the example to add the third conversation messages:

    ```sh
    python example.py 3
    ```

1. Run the example to get memory. Now you can see the summary of the second conversation as well:

    ```sh
    python example.py
    {'results': [{'conversation_id': 'conv_2', 'user_id': 'user_1', 'created_at': '2024-10-31T11:57:46.544352', 'summary': 'ユーザーは誕生日の過ごし方を考えており、誕生日は7月18日であることを伝えました。AIはその日がずいぶん先であることに言及しましたが、ユーザーは20代最後の年であるため特別な日と考えています。食事のアイデアとして、ユーザーは野菜、とりわけキャベツが食べたいと述べ、AIは肉ではなく野菜を選んだことに驚いていました。'}, {'conversation_id': 'conv_1', 'user_id': 'user_1', 'created_at': '2024-10-31T11:57:32.333432', 'summary': 'ユーザーは旅行を計画しており、温泉を目的地に選ぶと話しています。AIはその選択に賛同し、近場の箱根を提案したユーザーに共感し、移動の疲れを避けることの重要性を述べました。キーワード: 温泉、旅行、箱根、移動。'}]}
    ```

As you can see, the memory is updated when a new conversation starts.


🎃👻🍬 Happy Halloween! 🎃👻🍬  
Enjoy coding with a touch of Halloween magic! 🧙‍♀️✨
