import os
import openai

from factory import db

from server.openai_utils import get_samurai_claus_profile
from server.model import GPTPromptInstruction, Member
from server.constants import OpenAIMessageTypesEnum

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

    def generate_text_as_samurai_claus(self, prompt, member_name, temperature=0.7):
        """
        Generates text as Samurai Claus based on the given prompt.

        Args:
            prompt (str): The prompt to send to OpenAI.
            temperature (float, optional): Controls randomness in the response. Defaults to 0.7.

        Returns:
            str: The generated text response from OpenAI.
        """
        conversation_history = []
        conversation_history.append({
            "role": "system", 
            "content": get_samurai_claus_profile(member_name),
        })
        address_prompt = "Please ask the participant you are speaking to (me) to provide their shipping address."
        conversation_history.append({"role": "user", "content": prompt})
        chat_completion = openai.chat.completions.create(
            model="gpt-4",
            messages=conversation_history
        )
        # print('raw chat_completion', chat_completion)
        # Extract the latest response from Samurai Claus
        samurai_response = chat_completion.choices[0].message.content
        return samurai_response

    def chat_with_samurai_claus(
            self,
            user_message,
            to_number,
            member_id,
            conversation_history=[],
            message_type='chat',
        ):
        print('message_type', message_type.value)
        """
        Have a conversation with Samurai Claus using OpenAI's chat completions.

        Args:
            user_message (str): The latest message from the user.
            conversation_history (list): The history of the conversation so far.

        Returns:
            str: The latest response from Samurai Claus.
        """
        member = (
            db.session.query(Member)
            .filter(Member.id == member_id)
            .one()
        )
        member_name = member.name
        from server.message_queue_handler import MessageQueueHandler
        # Add the latest user message to the conversation history
        conversation_history.append({
            "role": "system", 
            "content": get_samurai_claus_profile(member_name),
        })
        if message_type == OpenAIMessageTypesEnum.CHAT:
            conversation_history.append({"role": "user", "content": user_message})
        else:
            prompt = (
                db.session.query(GPTPromptInstruction)
                .filter(GPTPromptInstruction.key == message_type.value)
                .one()
            )
            conversation_history.append({"role": "user", "content": prompt.prompt_template})
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

# Usage example:
# client = OpenAIClient()
# response = client.generate_response("Hello, this is Samurai Claus. How can I assist you?")
# print(response)
