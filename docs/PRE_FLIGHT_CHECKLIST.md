# Pre-Flight Checklist: Video Generation Readiness

**Last Updated**: After Audio System Migration
**Status**: ✅ Ready for Video Generation

## 🎯 Quick Status

| Component | Status | Notes |
|-----------|--------|-------|
| Audio System | ✅ Ready | Minimax primary + full fallback chain |
| Orchestration | ✅ Ready | Updated to use EnhancedVoiceGenerator |
| Pipeline | ✅ Ready | Updated to use EnhancedVoiceGenerator |
| Configuration | ✅ Ready | Both config files updated |
| Documentation | ✅ Ready | Setup guides created |
| Testing | ✅ Ready | Test script available |

---

## ✅ Completed Work

### 1. Audio System Migration (DONE)
- ✅ Added Minimax TTS as primary service
- ✅ Added KittenTTS as free fallback
- ✅ Deprecated ElevenLabs (kept in code)
- ✅ Updated fallback chain: `minimax → hume → openai → kittentts → gtts`
- ✅ Created `enhanced_audio_generator.py` with all services

### 2. Pipeline Integration (DONE)
- ✅ Updated `orchestration.py` to use `EnhancedVoiceGenerator`
- ✅ Updated `pipeline.py` to use `EnhancedVoiceGenerator`
- ✅ Both files now use full fallback chain automatically
- ✅ Text preprocessing (pronunciation maps) preserved

### 3. Configuration (DONE)
- ✅ `config.json` - Added Minimax and voice settings
- ✅ `config_enhanced.json` - Complete configuration
- ✅ Fallback chains defined in both files
- ✅ All service credentials sections added

### 4. Documentation & Testing (DONE)
- ✅ `AUDIO_SETUP_GUIDE.md` - Comprehensive setup instructions
- ✅ `AUDIO_MIGRATION_SUMMARY.md` - Migration details
- ✅ `test_audio_setup.py` - Verification script
- ✅ `PRE_FLIGHT_CHECKLIST.md` - This file

---

## 🔧 Required Configuration

### Minimum Required (For Video Generation)

Add to `config.json`:

```json
{
  "minimax": {
    "api_key": "YOUR_MINIMAX_API_KEY",
    "group_id": "YOUR_MINIMAX_GROUP_ID"
  },
  "hume_ai": {
    "api_key": "YOUR_HUME_API_KEY",
    "secret_key": "YOUR_HUME_SECRET_KEY",
    "use_hume": true
  }
}
```

**Where to get credentials:**
- **Minimax**: https://platform.minimaxi.com/user-center/basic-information
  - Get API Key and Group ID
  - Uses existing video token balance
- **Hume.ai**: https://dev.hume.ai (backup service)
  - Already configured in your current setup

### Optional (For Testing)

Run verification:
```bash
python test_audio_setup.py
```

Expected output: Shows service status and generates test audio

### Optional (Free Fallback)

If you want a free self-hosted option:

```bash
pip install kittentts
kittentts-server
```

Then verify it's running:
```bash
curl http://localhost:5000/health
```

---

## 🚀 Ready to Generate Video

### Option 1: Full Pipeline (Recommended)

```bash
# Standard run with github_urls.txt
python run_pipeline.py

# With custom input
python run_pipeline.py --input my_repos.txt

# Skip parsing (use existing posts_data.json)
python run_pipeline.py --skip-parse
```

### Option 2: Manual Prefect Run

```bash
# Start Prefect server if not running
./START_PREFECT_SERVER.sh

# Run orchestration
./run_with_prefect.sh orchestration
```

### Option 3: Direct Python

```bash
# Phase 1: Parse URLs
python simple_parser.py github_urls.txt

# Phase 2: Run orchestration
python -c "from orchestration import run_orchestration; run_orchestration()"
```

---

## 🧪 Pre-Generation Testing

Before generating a full video, test the audio system:

```bash
python test_audio_setup.py
```

**What it does:**
1. Tests the complete fallback chain
2. Generates test audio file
3. Shows which services are configured
4. Displays current fallback order
5. Plays audio (if possible)

**Expected output:**
```
======================================================================
🔊 AUDIO SERVICE VERIFICATION
======================================================================

Test text: Welcome to OpenSourceScribes. Testing audio generation.

Testing complete fallback chain...
----------------------------------------------------------------------

🎙️ Attempting MINIMAX...
🎙️ Minimax TTS: Welcome to OpenSourceScribes. Testing au...
   ✅ Minimax TTS generated (voice: male-1, speed: 1.0x)
======================================================================
✅ SUCCESS! Audio generated: test_audio_verification.mp3
======================================================================
```

---

## ⚠️ Legacy Files (Not Used by Main Pipeline)

These files have their own audio logic but are **not** used by the main pipeline:

- `video_maker.py` - Legacy generator
- `single_project_video.py` - Single project tool
- `extended_project_video.py` - Extended version
- `video_maker_with_shorts.py` - Dual video creator

**You don't need to update these** unless you specifically use them directly. The main pipeline uses `orchestration.py` which is now fully updated.

---

## 📊 Expected Behavior

### Audio Generation Flow

1. **Primary**: Minimax TTS
   - Uses video token balance
   - Expected to succeed

2. **Backup**: Hume.ai
   - If Minimax fails/credentials missing
   - Your existing Hume credits will be used

3. **Backup**: OpenAI TTS
   - If Hume also fails
   - Requires OpenAI API key in config

4. **Free**: KittenTTS (if you set it up)
   - No API costs
   - Must have server running locally

5. **Emergency**: gTTS
   - Always available
   - Robotic but functional

**Result**: Audio will always be generated, one way or another!

---

## 📝 Post-Generation Checklist

After video generation completes successfully:

- [ ] Check `deliveries/MM-DD/` folder for output
- [ ] Verify audio quality in generated video
- [ ] Check `test_audio_verification.mp3` was created
- [ ] Review logs for any warnings/errors
- [ ] Update this checklist with any issues found

---

## 🆘 Troubleshooting

### If audio generation fails completely:

1. Run test script:
   ```bash
   python test_audio_setup.py
   ```

2. Check config.json has Minimax credentials

3. Verify Prefect server is running:
   ```bash
   ./START_PREFECT_SERVER.sh
   ```

4. Check logs in terminal output

### If Minimax fails:

- Verify API key and Group ID are correct
- Check token balance at minimax.console
- Falls back to Hume.ai automatically

### If you see "ElevenLabs is deprecated":

- This is normal - it's in the code but not used
- Your audio is still generated via Minimax/Hume

---

## ✨ You're Ready!

**No more work needed.** The system is ready to generate videos with:

- ✅ Minimax TTS as primary (using video tokens)
- ✅ Full fallback chain (Hume → OpenAI → Kitten → gTTS)
- ✅ Updated orchestration and pipeline
- ✅ Complete configuration
- ✅ Test script for verification

**Next step**: Run your video generation command!

```bash
python run_pipeline.py
```

---

**System Status**: ✅ **PRODUCTION READY**

**Date**: 2025-01-07
**Version**: Audio System v2.0 (Minimax Primary)
