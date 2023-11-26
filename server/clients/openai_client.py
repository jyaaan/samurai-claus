import os
import openai

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

class OpenAIClient:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
    
    def get_models(self):
        return openai.Model.list()

    def generate_response(self, prompt, model="gpt-4", max_tokens=10000, temperature=0.7):
        """
        Generates a response from OpenAI based on the given prompt.

        Args:
            prompt (str): The prompt to send to OpenAI.
            model (str, optional): The model to use for the response. Defaults to "text-davinci-003".
            max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 150.
            temperature (float, optional): Controls randomness in the response. Defaults to 0.7.

        Returns:
            str: The generated text response from OpenAI.
        """
        try:
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(f"Error in generating response: {e}")
            return None

    def chat_with_samurai_claus(
            self,
            user_message,
            to_number,
            member_id,
            conversation_history=[]
        ):
        """
        Have a conversation with Samurai Claus using OpenAI's chat completions.

        Args:
            user_message (str): The latest message from the user.
            conversation_history (list): The history of the conversation so far.

        Returns:
            str: The latest response from Samurai Claus.
        """
        member_name = 'John'
        from server.message_queue_handler import MessageQueueHandler
        # Add the latest user message to the conversation history
        conversation_history.append({
            "role": "system", 
            "content": f"""
            You are Samurai Claus, where samurai wisdom meets Santa's cheer with a hint of Hawaiian aloha. Your responses should be brief yet meaningful, reflecting the calm of a samurai and the joy of Santa. Speak with a mix of festive cheer and ancient wisdom, using phrases like 'Merry Bushido', 'Season's Greetings, Samurai Spirit', 'Leis of Aloha, Lanterns of Light', 'Tinsel and Tenets of Bushido', and 'Aloha and Konnichiwa' but keep it concise.

            Share your love for serene, reflective holiday activities, like meditating on gratitude or enjoying the simple joy of gift-giving, in a few, carefully chosen words. Your humor should be light and family-friendly, and your advice practical yet inspiring.

            Your role is spreading holiday cheer with honor and discipline, guiding the Secret Santa process with wisdom and a touch of festive fun. Focus on the joy of connecting people in a joyful and meaningful way, embodying the spirit of both a samurai and Santa, in a succinct and engaging manner.

            You are an AI agent made to facilitate a family's secret santa gift exchange.

            You are speaking to {member_name}, who is a participant in the Secret Santa gift exchange.
            """
        })


        conversation_history.append({"role": "user", "content": user_message})
        try:
            chat_completion = openai.chat.completions.create(
                model="gpt-4",
                messages=conversation_history
            )
            print('raw chat_completion', chat_completion)
            # Extract the latest response from Samurai Claus
            samurai_response = chat_completion.choices[0].message.content

            # Add the response to the conversation history
            conversation_history.append({"role": "assistant", "content": samurai_response})
            print('conversation_history', conversation_history)
            print('samurai_response', samurai_response)
            MessageQueueHandler.enqueue_outbound_message(
                to_number=to_number,
                body=samurai_response,
                member_id=member_id
            )
        except Exception as e:
            print(f"Error in chat_with_samurai_claus: {e}")
            return None
    # Additional methods can be added here for more specific tasks, 
    # like handling Samurai Claus persona, etc.

# Usage example:
# client = OpenAIClient()
# response = client.generate_response("Hello, this is Samurai Claus. How can I assist you?")
# print(response)
