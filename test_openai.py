import openai

# Set your API key
openai.api_key = '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'

# Initialize the conversation history
conversation = [
    {"role": "system", "content": "You are a helpful assistant."}
]

print("Chatbot: Hello! You can start typing your questions (type 'exit' to quit).")

# Start the chat loop
while True:
    # Get user input
    user_input = input("You: ")
    
    # Exit the loop if the user types 'exit'
    if user_input.lower() == 'exit':
        print("Chatbot: Goodbye!")
        break

    # Add user message to conversation history
    conversation.append({"role": "user", "content": user_input})

    # Get the response from OpenAI
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=conversation
    )

    # Extract and print the assistant's reply using the .content attribute
    assistant_reply = response.choices[0].message.content
    print(f"Chatbot: {assistant_reply}")

    # Add assistant reply to conversation history
    conversation.append({"role": "assistant", "content": assistant_reply})
