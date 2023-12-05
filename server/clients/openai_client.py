import os
import openai
import json
import time

from factory import db

from server.openai_utils import get_samurai_claus_profile, get_inbound_analysis_prompt
from server.model import GPTPromptInstruction, Member, MessageLog
from server.constants import OpenAIMessageTypesEnum
from server.clients.ai_database_client import AIDatabaseClient

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

    def generate_text_as_samurai_claus(self, prompt, member_name, member_id, to_number, temperature=0.7):
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
        chat_history = self._generate_chat_history(member_id)
        conversation_history.extend(chat_history)
        address_prompt = "Please ask the participant you are speaking to (me) to provide their shipping address."
        conversation_history.append({"role": "user", "content": prompt})
        chat_completion = openai.chat.completions.create(
            model="gpt-4",
            messages=conversation_history,
        )
        # print('raw chat_completion', chat_completion)
        # Extract the latest response from Samurai Claus
        samurai_response = chat_completion.choices[0].message.content
        return samurai_response

    def send_template_message(self, message, to_number, member_id, attach_image=False):
        from server.message_queue_handler import MessageQueueHandler
        MessageQueueHandler.enqueue_outbound_message(
            to_number=to_number,
            body=message,
            member_id=member_id,
            attach_image=attach_image,
        )

    def chat_with_samurai_claus(
            self,
            user_message,
            to_number,
            member_id,
            conversation_history=[],
            message_type='chat',
            attach_image=False,
        ):
        # print('message_type', message_type.value)
        """
        Have a conversation with Samurai Claus using OpenAI's chat completions.

        Args:
            user_message (str): The latest message from the user.
            conversation_history (list): The history of the conversation so far.

        Returns:
            str: The latest response from Samurai Claus.
        """
        print('user_message', user_message)
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

        chat_history = self._generate_chat_history(member_id)

        conversation_history.extend(chat_history)
        conversation_history.append({"role": "user", "content": user_message})
        # else:
        #     prompt = (
        #         db.session.query(GPTPromptInstruction)
        #         .filter(GPTPromptInstruction.key == message_type.value)
        #         .one()
        #     )
        #     conversation_history.append({"role": "user", "content": prompt.prompt_template})
        try:
            chat_completion = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=conversation_history
            )
            # print('raw chat_completion', chat_completion)
            # Extract the latest response from Samurai Claus
            samurai_response = chat_completion.choices[0].message.content

            # Add the response to the conversation history
            conversation_history.append({"role": "assistant", "content": samurai_response})
            # print('conversation_history', conversation_history)
            print('samurai_response', samurai_response)
            MessageQueueHandler.enqueue_outbound_message(
                to_number=to_number,
                body=samurai_response,
                member_id=member_id,
                attach_image=attach_image,
            )
        except Exception as e:
            print(f"Error in chat_with_samurai_claus: {e}")
            return None
        
    def escalate_message(self, message_body, error_message):
        from server.message_queue_handler import MessageQueueHandler
        me = (
            db.session.query(Member)
            .filter(Member.name == 'John')
            .one()
        )
        combined_message = f"{error_message} - message: {message_body}"
        MessageQueueHandler.enqueue_outbound_message(
            to_number=me.phone,
            body=combined_message,
            member_id=me.id,
        )
        
    def analyze_inbound_message(
        self,
        member_id,
        message_body,
        to_number,
        from_number,
    ):
        """
        Analyze an inbound message from a member.

        Args:
            message_body (str): The body of the message.
            member_id (int): The ID of the member.

        Returns:
            str: The type of message.
        """
        ai_db_client = AIDatabaseClient()
        member = (
            db.session.query(Member)
            .filter(Member.id == member_id)
            .one()
        )
        conversation_history = []
        conversation_history.append({
            "role": "system", 
            "content": get_samurai_claus_profile(member.name),
        })
        chat_history = self._generate_chat_history(member_id)
        conversation_history.extend(chat_history)
        conversation_history.append({"role": "user", "content": get_inbound_analysis_prompt(message_body, member_id)})
        try:
            chat_completion = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=conversation_history,
            )
            actions = chat_completion.choices[0].message.content
            actions = actions.replace('```json\n', '').replace('```', '').strip()
            print('actions before loads', actions)
            if actions:
                actions = json.loads(actions)
            print('actions', actions)
            for action in actions:
                function = action['function']
                if function == 'chat':
                    self.chat_with_samurai_claus(
                        user_message=message_body,
                        to_number=member.phone,
                        member_id=member_id,
                        message_type=OpenAIMessageTypesEnum.CHAT,
                    )
                elif function == 'escalate':
                    self.escalate_message(
                        message_body=message_body,
                        error_message=action['message'],
                    )
                    time.sleep(20)
                    escalastion_reply = "Please tell the participant you are speaking to (me) that their message has been escalated to the Samurai Claus team and they will be in touch shortly."
                    self.chat_with_samurai_claus(
                        user_message=escalastion_reply,
                        to_number=member.phone,
                        member_id=member_id,
                        attach_image=True,
                    )
                elif function == 'request_address':
                    santee_address = ai_db_client.get_santee_address(member_id)
                    if santee_address:
                        address_reply = f"Please tell the participant you are speaking to (me)  that their Secret Santee's address is: {santee_address}"
                        self.generate_text_as_samurai_claus(
                            prompt=address_reply,
                            member_name=member.name,
                            member_id=member_id,
                        )
                    else:
                        address_reply = "Please tell the participant you are speaking to (me) that their Secret Santee has not yet provided their address and that You have sent a reminder to the Secret Santee."
                        self.chat_with_samurai_claus(
                            user_message=address_reply,
                            to_number=member.phone,
                            member_id=member_id,
                        )
                        time.sleep(20)
                        santee_details = ai_db_client.get_my_santee_details(member_id)
                        address_reminder = "Please ask the participant you are speaking to (me) to provide their shipping address when they are able to.  Be polite."
                        self.chat_with_samurai_claus(
                            user_message=address_reminder,
                            to_number=santee_details['phone'],
                            member_id=santee_details['id'],
                            attach_image=True,
                        )
                elif function == 'request_wishlist':
                    santee_wishlist = ai_db_client.get_santee_wishlist(member_id)
                    if santee_wishlist:
                        wishlist_reply = f"Please tell the participant you are speaking to (me) that their Secret Santee's wishlist is: {santee_wishlist}. Please don't modify the wishlist too much, as in don't be too whimsical here."
                        self.chat_with_samurai_claus(
                            user_message=wishlist_reply,
                            to_number=member.phone,
                            member_id=member_id,
                        )
                    else:
                        wishlist_reply = "Please tell the participant you are speaking to (me) that their Secret Santee has not yet provided their wishlist and that You have sent a reminder to their Secret Santee."
                        self.chat_with_samurai_claus(
                            user_message=wishlist_reply,
                            to_number=member.phone,
                            member_id=member_id,
                        )
                        time.sleep(20)
                        santee_details = ai_db_client.get_my_santee_details(member_id)
                        wishlist_reminder = "Please remind the participant you are speaking to (me) to provide their wishlist items when they are able to. Be polite and encouraging."
                        self.chat_with_samurai_claus(
                            user_message=wishlist_reminder,
                            to_number=santee_details['phone'],
                            member_id=santee_details['id'],
                            attach_image=True,
                        )
                elif function == 'process_my_wishlist':
                    my_wishlist = action['args']['wishlist']
                    ai_db_client.write_my_wishlist(member_id, my_wishlist)
                    wishlist_confirmation = f"Please tell the participant you are speaking to (me) that their wishlist has been updated to: {my_wishlist}"
                    self.chat_with_samurai_claus(
                        user_message=wishlist_confirmation,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                    time.sleep(20)
                    santa_details = ai_db_client.get_my_santa_details(member_id)
                    santa_wishlist_notice = f"Please ask the participant you are speaking to (me) that their Secret Santee has completed a wishlist: {my_wishlist}. Please don't modify the wishlist too much, as in don't be too whimsical here. Please preserve links!"
                    self.chat_with_samurai_claus(
                        user_message=santa_wishlist_notice,
                        to_number=santa_details['phone'],
                        member_id=santa_details['id'],
                        attach_image=True,
                    )
                    
                elif function == 'process_my_address':
                    my_address = action['args']['address']
                    ai_db_client.write_my_address(member_id, my_address)
                    address_confirmation = f"Please tell the participant you are speaking to (me) that their address has been updated to: {my_address}. Provide a fun fact of their city if you can find one."
                    self.chat_with_samurai_claus(
                        user_message=address_confirmation,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                    time.sleep(20)
                    santa_details = ai_db_client.get_my_santa_details(member_id)
                    santa_address_notice = f"Please ask the participant you are speaking to (me) that their Secret Santee has filled out their address: {my_address}"
                    self.chat_with_samurai_claus(
                        user_message=santa_address_notice,
                        to_number=santa_details['phone'],
                        member_id=santa_details['id'],
                        attach_image=True,
                    )
                    
                elif function == 'remind_my_santee':
                    santee_details = ai_db_client.get_my_santee_details(member_id)
                    my_santee_reminder = f"Please tell the participant you are speaking to (me) that their Secret Santee for this year is: {santee_details['name']}"
                    self.chat_with_samurai_claus(
                        user_message=my_santee_reminder,
                        to_number=member.phone,
                        member_id=member.id,
                        attach_image=True,
                    )
                elif function == 'remind_my_address':
                    my_address = ai_db_client.get_my_address(member_id)
                    my_address_reminder = None
                    if my_address:
                        my_address_reminder = f"Please tell the participant you are speaking to (me) that their address is: {my_address}. and they can update this by telling you their new address."
                    else:
                        my_address_reminder = "Please tell the participant you are speaking to (me) that they have not yet provided their address and to let them know that they should provide an address quickly so their Secret Santa can send them their gift on time."
                    
                    self.chat_with_samurai_claus(
                        user_message=my_address_reminder,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                elif function == 'remind_my_wishlist':
                    my_wishlist = ai_db_client.get_my_wishlist(member_id)
                    my_wishlist_reminder = None
                    if my_wishlist:
                        my_wishlist_reminder = f"Please tell the participant you are speaking to (me) that their wishlist is: {my_wishlist}. and they can update this by informing you of any changes."
                    else:
                        my_wishlist_reminder = "Please tell the participant you are speaking to (me) that they have not yet provided their wishlist and to let them know that they should provide a wishlist quickly so their Secret Santa can send them their gift on time."
                    self.chat_with_samurai_claus(
                        user_message=my_wishlist_reminder,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                elif function == 'remind_my_todo':
                    my_wishlist = ai_db_client.get_my_wishlist(member_id)
                    my_address = ai_db_client.get_my_address(member_id)
                    print('mywishlist', my_wishlist)
                    print('mywishlisttype', type(my_wishlist))
                    print('myaddress', my_address)
                    print('myaddresstype', type(my_address))
                    todo_reminder = None
                    if not my_wishlist and not my_address:
                        todo_reminder = "Please tell the participant you are speaking to (me) that they should provide their wishlist and address as soon as possible."
                    elif not my_wishlist and my_address:
                        todo_reminder = "Please tell the participant you are speaking to (me) that they should provide their wishlist as soon as possible."
                    elif my_wishlist and not my_address:
                        todo_reminder = "Please tell the participant you are speaking to (me) that they should provide their address as soon as possible."
                    else:
                        todo_reminder = "Please tell the participant you are speaking to (me) that they have already provided their wishlist and address. Thank you!"
                    
                    self.chat_with_samurai_claus(
                        user_message=todo_reminder,
                        to_number=member.phone,
                        member_id=member_id,
                        attach_image=True,
                    )
                elif function == 'santee_question':
                    santee_details = ai_db_client.get_my_santee_details(member_id)
                    question = action['args']['question']
                    question_prompt = f"Please tell the participant you are speaking to (me) that their Secret Santa asked them a question: {question}"
                    self.chat_with_samurai_claus(
                        user_message=question_prompt,
                        to_number=santee_details['phone'],
                        member_id=santee_details['id'],
                        attach_image=True,
                    )
                    time.sleep(20)
                    santee_question_confirmation = f"Please tell the participant you are speaking to (me) that you have relayed their question to their Santee."
                    self.chat_with_samurai_claus(
                        user_message=santee_question_confirmation,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                elif function == 'santee_answer':
                    santa_details = ai_db_client.get_my_santa_details(member_id)
                    answer = action['args']['answer']
                    answer_prompt = f"Please tell the participant you are speaking to (me) that their Secret Santee answered their question with: {answer}"
                    self.chat_with_samurai_claus(
                        user_message=answer_prompt,
                        to_number=santa_details['phone'],
                        member_id=santa_details['id'],
                        attach_image=True,
                    )
                    time.sleep(20)
                    santee_answer_confirmation = f"Please tell the participant you are speaking to (me) that you have relayed their answer to their Secret Santa."
                    self.chat_with_samurai_claus(
                        user_message=santee_answer_confirmation,
                        to_number=member.phone,
                        member_id=member_id,
                    )
                else:
                    error_message = f"Error: unrecognized function {function} - message: {message_body} - from gpt: {action}"
                    self.escalate_message(
                        message_body=message_body,
                        error_message=error_message,
                    )
                    time.sleep(20)
                    escalastion_reply = "Please tell the participant you are speaking to (me) that you weren't able to understand their message and that You have escalated their message to the Samurai Claus team."
                    self.chat_with_samurai_claus(
                        user_message=escalastion_reply,
                        to_number=member.phone,
                        member_id=member_id,
                    )

        except json.JSONDecodeError as e:
            error_message = f"Error: JSON parsing error - message: {member_id}"
            self.escalate_message(
                message_body=message_body,
                error_message=error_message,
            )
            print(f"JSON parsing error: {e}")
        except Exception as e:
            error_message = f"exception: {e} - member_id: {member_id}"
            self.escalate_message(
                message_body=message_body,
                error_message=error_message,
            )
            print(f"Error in analyze_inbound_message: {e}")
            raise e
        return ''
        
    def _generate_chat_history(self, member_id):
        # this will read all past delivered messages between samurai claus
        # and the member specified
        valid_statuses = [
            'delivered',
            'sent',
            'received',
        ]
        message_history = (
            db.session.query(MessageLog)
            .filter(
                MessageLog.member_id == member_id,
                MessageLog.status.in_(valid_statuses)
            )
            .order_by(MessageLog.created_ts)
            .all()
        )
        conversation_history = []
        for message in message_history:
            if message.direction == 'inbound':
                conversation_history.append({"role": "user", "content": message.message_body})
            else:
                conversation_history.append({"role": "assistant", "content": message.message_body})
        
        return conversation_history

# Usage example:
# client = OpenAIClient()
# response = client.generate_response("Hello, this is Samurai Claus. How can I assist you?")
# print(response)
