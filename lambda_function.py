import os
import json
import logging
import base64

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
 
import firebase_admin
from firebase_admin import credentials, firestore
 
from besso.checkout import checkout


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

secret_key_b64 = os.getenv("SECRET_KEY")
firestore_client = None
 
if secret_key_b64:
    try:

        b64_string = secret_key_b64.strip()
        missing_padding = len(b64_string) % 4
        if missing_padding:
            b64_string += '=' * (4 - missing_padding)
        decoded_bytes = base64.b64decode(b64_string)
        secret_key_json = decoded_bytes.decode('utf-8')
        creds_dict = json.loads(secret_key_json.strip())
        
        cred = credentials.Certificate(creds_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized successfully from Base64 secret")
        firestore_client = firestore.client()
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin from Base64: {e}", exc_info=True)
else:
    logger.error("SECRET_KEY env var is missing!")

MESSAGES = {
    "LAUNCH": {
        "en": "Hello. This is the front desk. How may I help you?",
        "ja": "こんにちは。こちらはフロントです。ご用件をお伺いいたします。",
        "ar": "مرحبًا، هذا هو مكتب الاستقبال. كيف يمكنني مساعدتك؟",
        "de": "Hallo, hier ist die Rezeption. Wie kann ich Ihnen helfen؟"
    },
    "CHECKOUT": {
        "en": "You have been checked out.",
        "ja": "チェックアウトしました",
        "ar": "تم تسجيل الخروج.",
        "de": "Sie wurden ausgecheckt."
    },
    "HELP": {
        "en": "How can I assist you?",
        "ja": "どうされましたか？",
        "ar": "كيف يمكنني مساعدتك؟",
        "de": "Wie kann ich Ihnen helfen?"
    },
    "FALLBACK": {
        "en": "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?",
        "ja": "すみません、よくわかりません。挨拶かヘルプを言ってください。どのようにお手伝いできますか？",
        "ar": "همم، لست متأكدًا. يمكنك أن تقول مرحبًا أو مساعدة. ماذا تريد أن تفعل؟",
        "de": "Ähm, ich bin nicht sicher. Du kannst Hallo oder Hilfe sagen. Wie kann ich dir helfen؟"
    },
    "ERROR": {
        "en": "I'm sorry, there was an issue. Please try again.",
        "ja": "すみません。問題が発生しました。もう一度お願いいたします。",
        "ar": "آسف، حدثت مشكلة. حاول مرة أخرى.",
        "de": "Entschuldigung, es gab ein Problem. Bitte versuche es noch einmal."
    }
}
 
def get_language(locale: str) -> str:
    if locale.startswith("ja"):
        return "ja"
    if locale.startswith("ar"):
        return "ar"
    if locale.startswith("de"):
        return "de"
    return "en"
 

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("LaunchRequest")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        locale = handler_input.request_envelope.request.locale
        lang = get_language(locale)
        speak = MESSAGES["LAUNCH"][lang]
        return handler_input.response_builder.speak(speak).ask(speak).response
 
class CheckOutIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("CheckOutIntent")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        locale = handler_input.request_envelope.request.locale
        lang = get_language(locale)
 
        if firestore_client is None:
            logger.error("Firestore client is not initialized")
            return handler_input.response_builder.speak(MESSAGES["ERROR"][lang]).response
 
        device_id = handler_input.request_envelope.context.system.device.device_id
        logger.info(f"CheckOut requested from deviceId={device_id}")
 
        docs = list(
            firestore_client
              .collection("CheckInCheckOut")
              .where("deviceId", "==", device_id)
              .limit(1)
              .stream()
        )
 
        if not docs:
            error_speak = {
                "en": "Sorry, I don’t know which building this is. Please contact the administrator.",
                "ja": "申し訳ありません。どのビルか認識できませんでした。管理者にご連絡ください。",
                "ar": "آسف، لا أعرف أي مبنى هذا. يرجى الاتصال بالمسؤول.",
                "de": "Entschuldigung, mir ist nicht bekannt, um welches Gebäude es sich handelt. Bitte kontaktieren Sie den Administrator."
            }[lang]
            return handler_input.response_builder.speak(error_speak).response
 
        building_id = docs[0].id
        
        try:
            success = checkout(firestore_client, building_id, device_id)
        except Exception as e:
            logger.error(f"Unhandled exception in checkout: {e}", exc_info=True)
            success = False

        speak_output = MESSAGES["CHECKOUT"][lang] if success else MESSAGES["ERROR"][lang]
        return handler_input.response_builder.speak(speak_output).response
 
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        locale = handler_input.request_envelope.request.locale
        lang = get_language(locale)
        speak = MESSAGES["HELP"][lang]
        return handler_input.response_builder.speak(speak).ask(speak).response
 
class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
            ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )
 
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.speak("").response
 
class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        locale = handler_input.request_envelope.request.locale
        lang = get_language(locale)
        speech = MESSAGES["FALLBACK"][lang]
        reprompt = MESSAGES["HELP"][lang]
        return handler_input.response_builder.speak(speech).ask(reprompt).response
 
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response
 
class IntentReflectorHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("IntentRequest")(handler_input)
 
    def handle(self, handler_input: HandlerInput) -> Response:
        intent_name = ask_utils.get_intent_name(handler_input)
        speak = f"You just triggered {intent_name}."
        return handler_input.response_builder.speak(speak).response
 
class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True
 
    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(exception, exc_info=True)
        locale = handler_input.request_envelope.request.locale
        lang = get_language(locale)
        speak = MESSAGES["ERROR"][lang]
        return handler_input.response_builder.speak(speak).ask(speak).response
 

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CheckOutIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()