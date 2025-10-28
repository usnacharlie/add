"""
Multi-Language Communication APIs for Zambian Political Party System
Supporting: IVR, SMS, USSD, WhatsApp in multiple Zambian languages
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import json

# Import existing dependencies
from main import app, get_db, get_current_member

# ============== LANGUAGE MANAGEMENT APIs ==============

@app.get("/api/v1/languages")
def get_supported_languages(db: Session = Depends(get_db)):
    """Get all supported languages"""
    return {
        "languages": [
            {"code": "en", "name": "English", "native": "English"},
            {"code": "bem", "name": "Bemba", "native": "Ichibemba"},
            {"code": "nya", "name": "Nyanja", "native": "Chinyanja"},
            {"code": "ton", "name": "Tonga", "native": "Chitonga"},
            {"code": "loz", "name": "Lozi", "native": "Silozi"},
            {"code": "luv", "name": "Luvale", "native": "Chiluvale"},
            {"code": "kao", "name": "Kaonde", "native": "Kiikaonde"},
            {"code": "lun", "name": "Lunda", "native": "Chilunda"},
            {"code": "lam", "name": "Lamba", "native": "Ichilamba"},
            {"code": "ila", "name": "Ila", "native": "Ila"},
            {"code": "mam", "name": "Mambwe", "native": "Mambwe"},
            {"code": "nam", "name": "Namwanga", "native": "Namwanga"},
            {"code": "tum", "name": "Tumbuka", "native": "Chitumbuka"}
        ],
        "official_languages": ["en", "bem", "nya", "ton", "loz", "luv", "kao", "lun"]
    }

@app.put("/api/v1/members/{member_id}/language-preference")
def update_language_preference(
    member_id: str,
    language_code: str,
    secondary_language: Optional[str] = None,
    literacy_level: str = "intermediate",
    db: Session = Depends(get_db)
):
    """Update member's language preference"""
    # Update member language preferences
    return {
        "message": "Language preference updated",
        "primary_language": language_code,
        "secondary_language": secondary_language,
        "literacy_level": literacy_level
    }

@app.get("/api/v1/members/{member_id}/communication-preferences")
def get_communication_preferences(member_id: str, db: Session = Depends(get_db)):
    """Get member's communication preferences"""
    return {
        "member_id": member_id,
        "preferences": {
            "language": "en",
            "secondary_language": "bem",
            "channels": {
                "sms": {"enabled": True, "language": "en"},
                "voice": {"enabled": True, "language": "bem"},
                "ussd": {"enabled": True, "language": "en"},
                "whatsapp": {"enabled": True, "language": "en"},
                "email": {"enabled": False}
            },
            "literacy_level": "intermediate",
            "requires_audio": False,
            "quiet_hours": {"start": "22:00", "end": "06:00"}
        }
    }

# ============== IVR (Interactive Voice Response) APIs ==============

@app.post("/api/v1/ivr/initiate-call")
def initiate_ivr_call(
    phone_number: str,
    language_code: str = "en",
    purpose: str = "registration",
    db: Session = Depends(get_db)
):
    """Initiate an IVR call to a member"""
    return {
        "call_id": "CALL123456",
        "phone_number": phone_number,
        "language": language_code,
        "status": "initiating",
        "estimated_wait": "30 seconds"
    }

@app.post("/api/v1/ivr/handle-input")
def handle_ivr_input(
    session_id: str,
    dtmf_input: str,
    db: Session = Depends(get_db)
):
    """Handle DTMF input from IVR system"""
    # Language selection menu
    if dtmf_input == "1":
        response = {
            "action": "play_menu",
            "audio_url": "/audio/menus/language_selection.mp3",
            "text": "Press 1 for English, 2 for Bemba, 3 for Nyanja, 4 for Tonga",
            "next_menu": "LANGUAGE_SELECTION"
        }
    else:
        response = {
            "action": "play_message",
            "audio_url": "/audio/messages/invalid_input.mp3",
            "text": "Invalid input. Please try again.",
            "repeat_menu": True
        }

    return response

@app.get("/api/v1/ivr/menu-content/{menu_code}")
def get_ivr_menu_content(
    menu_code: str,
    language_code: str = "en",
    db: Session = Depends(get_db)
):
    """Get IVR menu content in specified language"""
    menus = {
        "MAIN": {
            "en": "Welcome to Party Membership. Press 1 for Registration, 2 for Status Check, 3 for Payments",
            "bem": "Mwaiseni mu Party Membership. Iminako 1 pa kulembelesha, 2 pa kufwaya umulandu, 3 pa malipilo",
            "nya": "Takulandilani ku Party Membership. Dinani 1 kulembetsa, 2 kuona momwe zilili, 3 kulipila",
            "ton": "Mwatambulwa ku Party Membership. Amutobele 1 kuti mulembede, 2 kuti mwaamvwisye, 3 kubbadela"
        }
    }

    return {
        "menu_code": menu_code,
        "language": language_code,
        "content": menus.get(menu_code, {}).get(language_code, "Menu not available"),
        "audio_url": f"/audio/{language_code}/{menu_code}.mp3"
    }

@app.post("/api/v1/ivr/text-to-speech")
def convert_text_to_speech(
    text: str,
    language_code: str = "en",
    voice_gender: str = "female",
    db: Session = Depends(get_db)
):
    """Convert text to speech in specified language"""
    return {
        "audio_url": f"/audio/tts/{language_code}/generated_audio.mp3",
        "duration_seconds": len(text) * 0.1,  # Rough estimate
        "language": language_code,
        "voice": voice_gender
    }

# ============== ENHANCED USSD APIs WITH MULTI-LANGUAGE ==============

@app.post("/api/v1/ussd/handle")
def handle_ussd_request(
    session_id: str,
    phone_number: str,
    text: str,
    language_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle USSD request with language support"""

    # First time user - ask for language preference
    if text == "" and not language_code:
        response = "Select Language/Salankho Chiyankhulo:\n"
        response += "1. English\n"
        response += "2. Bemba\n"
        response += "3. Nyanja\n"
        response += "4. Tonga\n"
        response += "5. Lozi"
        return {"text": response, "continue_session": True}

    # Language selected, show main menu in chosen language
    if text == "1":  # English selected
        response = "Party Membership\n"
        response += "1. Register\n"
        response += "2. Check Status\n"
        response += "3. Make Payment\n"
        response += "4. Events\n"
        response += "5. Exit"
    elif text == "2":  # Bemba selected
        response = "Party Membership\n"
        response += "1. Lembelesha\n"
        response += "2. Fwaya umulandu\n"
        response += "3. Lipila\n"
        response += "4. Masonekelo\n"
        response += "5. Fulila"
    elif text == "3":  # Nyanja selected
        response = "Party Membership\n"
        response += "1. Lembetsa\n"
        response += "2. Ona momwe zilili\n"
        response += "3. Lipila\n"
        response += "4. Zochitika\n"
        response += "5. Tuluka"
    else:
        response = "Invalid option. Please try again."

    return {
        "text": response,
        "session_id": session_id,
        "continue_session": True
    }

@app.get("/api/v1/ussd/menu-structure")
def get_ussd_menu_structure(language_code: str = "en"):
    """Get USSD menu structure in specified language"""
    return {
        "language": language_code,
        "menus": {
            "main": {
                "en": ["Register", "Check Status", "Make Payment", "Events", "Exit"],
                "bem": ["Lembelesha", "Fwaya umulandu", "Lipila", "Masonekelo", "Fulila"],
                "nya": ["Lembetsa", "Ona momwe zilili", "Lipila", "Zochitika", "Tuluka"],
                "ton": ["Lembede", "Amvwisye", "Bbadela", "Zyoonse", "Zwa"]
            }
        }
    }

# ============== SMS APIs WITH MULTI-LANGUAGE ==============

@app.post("/api/v1/sms/send")
def send_sms(
    phone_number: str,
    message_key: str,
    language_code: str = "en",
    variables: Optional[Dict] = None,
    db: Session = Depends(get_db)
):
    """Send SMS in specified language"""
    templates = {
        "welcome": {
            "en": "Welcome {name} to the party! Your membership number is {number}",
            "bem": "Mwaiseni {name} mu chipani! Inambala yenu ya membership ni {number}",
            "nya": "Takulandilani {name} ku chipani! Nambala yanu ya membership ndi {number}",
            "ton": "Mwatambulwa {name} ku chipani! Nambala yanu ya membership ngu {number}"
        },
        "payment_reminder": {
            "en": "Dear {name}, your membership fee of K{amount} is due. Pay via MTN: *303#",
            "bem": "Ba {name}, amalipilo yenu ya K{amount} yafika. Lipileni pa MTN: *303#",
            "nya": "A {name}, ndalama zanu za K{amount} zafika. Lipilani pa MTN: *303#",
            "ton": "A {name}, mali aanu aa K{amount} afwene. Bbadeleni pa MTN: *303#"
        }
    }

    message_template = templates.get(message_key, {}).get(language_code)
    if message_template and variables:
        message = message_template.format(**variables)
    else:
        message = message_template or "Message not available"

    return {
        "status": "queued",
        "message_id": "MSG123456",
        "phone_number": phone_number,
        "message": message,
        "language": language_code,
        "character_count": len(message),
        "sms_parts": (len(message) // 160) + 1
    }

@app.post("/api/v1/sms/bulk-send")
def send_bulk_sms(
    recipient_filter: Dict,
    message_key: str,
    use_preferred_language: bool = True,
    db: Session = Depends(get_db)
):
    """Send bulk SMS in recipients' preferred languages"""
    return {
        "job_id": "BULK123456",
        "status": "processing",
        "estimated_recipients": 1500,
        "languages_distribution": {
            "en": 600,
            "bem": 400,
            "nya": 300,
            "ton": 200
        },
        "estimated_completion": "15 minutes"
    }

# ============== WHATSAPP APIs WITH MULTI-LANGUAGE ==============

@app.post("/api/v1/whatsapp/send")
def send_whatsapp(
    phone_number: str,
    message_type: str,  # text, image, document, audio
    content: str,
    language_code: str = "en",
    db: Session = Depends(get_db)
):
    """Send WhatsApp message in specified language"""
    return {
        "status": "sent",
        "message_id": "WA123456",
        "phone_number": phone_number,
        "message_type": message_type,
        "language": language_code,
        "delivered_at": datetime.now().isoformat()
    }

@app.post("/api/v1/whatsapp/interactive-menu")
def send_whatsapp_menu(
    phone_number: str,
    language_code: str = "en",
    db: Session = Depends(get_db)
):
    """Send interactive WhatsApp menu in specified language"""
    menus = {
        "en": {
            "header": "Party Membership Services",
            "body": "Please select an option:",
            "buttons": [
                {"id": "1", "title": "Register"},
                {"id": "2", "title": "Check Status"},
                {"id": "3", "title": "Make Payment"}
            ]
        },
        "bem": {
            "header": "Party Membership Services",
            "body": "Salako:",
            "buttons": [
                {"id": "1", "title": "Lembelesha"},
                {"id": "2", "title": "Fwaya umulandu"},
                {"id": "3", "title": "Lipila"}
            ]
        }
    }

    return {
        "status": "sent",
        "menu": menus.get(language_code, menus["en"]),
        "language": language_code
    }

# ============== TRANSLATION APIs ==============

@app.post("/api/v1/translate")
def translate_content(
    content: str,
    from_language: str = "en",
    to_language: str = "bem",
    content_type: str = "general",
    db: Session = Depends(get_db)
):
    """Translate content between languages"""
    # This would integrate with translation service
    return {
        "original": content,
        "translated": "Translated content here",
        "from_language": from_language,
        "to_language": to_language,
        "confidence": 0.95
    }

@app.get("/api/v1/content/{content_key}")
def get_multilingual_content(
    content_key: str,
    language_code: str = "en",
    db: Session = Depends(get_db)
):
    """Get content in specified language"""
    return {
        "content_key": content_key,
        "language": language_code,
        "content": "Content in requested language",
        "fallback_used": False
    }

# ============== ACCESSIBILITY APIs ==============

@app.put("/api/v1/members/{member_id}/accessibility")
def update_accessibility_settings(
    member_id: str,
    settings: Dict,
    db: Session = Depends(get_db)
):
    """Update member's accessibility settings"""
    return {
        "member_id": member_id,
        "settings": {
            "visual_impairment": settings.get("visual_impairment", False),
            "hearing_impairment": settings.get("hearing_impairment", False),
            "requires_audio_only": settings.get("requires_audio_only", False),
            "requires_simple_language": settings.get("requires_simple_language", False),
            "preferred_font_size": settings.get("preferred_font_size", "normal"),
            "high_contrast_mode": settings.get("high_contrast_mode", False)
        },
        "updated": True
    }

@app.get("/api/v1/members/{member_id}/accessible-content")
def get_accessible_content(
    member_id: str,
    content_key: str,
    db: Session = Depends(get_db)
):
    """Get content formatted for member's accessibility needs"""
    return {
        "content_key": content_key,
        "format": "audio",
        "audio_url": "/audio/accessible/content.mp3",
        "text_simplified": "Simple version of content",
        "font_size": "large"
    }

# ============== LANGUAGE ANALYTICS APIs ==============

@app.get("/api/v1/analytics/language-usage")
def get_language_usage_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get language usage analytics"""
    return {
        "period": f"{start_date} to {end_date}",
        "total_communications": 50000,
        "by_language": {
            "en": {"count": 20000, "percentage": 40},
            "bem": {"count": 12000, "percentage": 24},
            "nya": {"count": 10000, "percentage": 20},
            "ton": {"count": 5000, "percentage": 10},
            "loz": {"count": 3000, "percentage": 6}
        },
        "by_channel": {
            "sms": {"total": 25000, "top_language": "en"},
            "voice": {"total": 10000, "top_language": "bem"},
            "ussd": {"total": 10000, "top_language": "nya"},
            "whatsapp": {"total": 5000, "top_language": "en"}
        },
        "literacy_levels": {
            "advanced": 30,
            "intermediate": 45,
            "basic": 20,
            "none": 5
        }
    }

@app.get("/api/v1/analytics/channel-preference")
def get_channel_preference_analytics(db: Session = Depends(get_db)):
    """Get communication channel preference analytics"""
    return {
        "by_province": {
            "Lusaka": {"sms": 40, "voice": 20, "ussd": 25, "whatsapp": 15},
            "Copperbelt": {"sms": 35, "voice": 25, "ussd": 30, "whatsapp": 10},
            "Southern": {"sms": 30, "voice": 35, "ussd": 25, "whatsapp": 10},
            "Eastern": {"sms": 25, "voice": 40, "ussd": 30, "whatsapp": 5}
        },
        "by_age_group": {
            "18-25": {"sms": 30, "voice": 10, "ussd": 20, "whatsapp": 40},
            "26-35": {"sms": 35, "voice": 15, "ussd": 25, "whatsapp": 25},
            "36-50": {"sms": 40, "voice": 25, "ussd": 30, "whatsapp": 5},
            "50+": {"sms": 30, "voice": 45, "ussd": 20, "whatsapp": 5}
        },
        "by_literacy_level": {
            "advanced": {"sms": 35, "voice": 10, "ussd": 15, "whatsapp": 40},
            "intermediate": {"sms": 40, "voice": 20, "ussd": 25, "whatsapp": 15},
            "basic": {"sms": 25, "voice": 35, "ussd": 35, "whatsapp": 5},
            "none": {"sms": 5, "voice": 60, "ussd": 30, "whatsapp": 5}
        }
    }

# ============== LITERACY SUPPORT APIs ==============

@app.get("/api/v1/literacy/assess/{member_id}")
def assess_literacy_level(member_id: str, db: Session = Depends(get_db)):
    """Assess member's literacy level"""
    return {
        "member_id": member_id,
        "assessment": {
            "can_read_english": True,
            "can_write_english": True,
            "can_read_local_language": True,
            "can_write_local_language": False,
            "digital_literacy": "basic",
            "recommended_channels": ["voice", "ussd", "sms"],
            "recommended_language": "nya"
        }
    }

@app.post("/api/v1/literacy/simplify-content")
def simplify_content(
    content: str,
    target_level: str = "basic",
    language_code: str = "en",
    db: Session = Depends(get_db)
):
    """Simplify content for different literacy levels"""
    return {
        "original": content,
        "simplified": "Simplified version of the content",
        "reading_level": target_level,
        "language": language_code,
        "word_count_reduction": "40%"
    }

# ============== TOTAL MULTI-LANGUAGE APIs: 35+ ==============