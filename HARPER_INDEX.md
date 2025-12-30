# 📚 Harper Documentation Index

Complete guide to Harper, Trapier Management's AI inbound call assistant.

---

## 🎤 What is Harper?

**Harper** is your AI receptionist for inbound calls. She:
- Answers calls professionally and warmly
- Qualifies prospects based on pain point, authority, and timeline
- Books discovery calls with Harold (Tuesday 10 AM or Thursday 2 PM ET)
- Handles 10+ industries with specific ROI data
- Manages objections naturally and conversationally
- Represents Trapier Management LLC professionally

**Harper's Job:** Book qualified meetings (not close deals)
**Harold's Job:** Close the deals in discovery calls

---

## 📖 Documentation Files

### 🚀 START HERE
**[HARPER_QUICK_REFERENCE.md](HARPER_QUICK_REFERENCE.md)** - One-page quick lookup
- Perfect for: During calls, quick training, reference card
- Contains: 5-step flow, ROI table, objections, voice rules
- Read time: 5 minutes

### 📋 COMPLETE TRAINING
**[HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md)** - Full operator training manual
- Perfect for: Comprehensive understanding, training new operators
- Contains: Detailed 5-step flow, all 10 industries, objection responses, voice/tone guidelines
- Read time: 30 minutes
- Pages: 40+

### 🎯 PROJECT OVERVIEW
**[HARPER_SETUP_COMPLETE.md](HARPER_SETUP_COMPLETE.md)** - What's complete and ready
- Perfect for: Understanding what's built, deployment status
- Contains: What's done, how Harper works, deployment instructions, metrics
- Read time: 15 minutes

### 💬 REAL EXAMPLES
**[HARPER_CONVERSATION_EXAMPLES.md](HARPER_CONVERSATION_EXAMPLES.md)** - 8 real conversation examples
- Perfect for: Learning by example, understanding flow in context
- Contains: 8 complete calls showing different scenarios and outcomes
- Read time: 20 minutes

### 📞 INITIAL OVERVIEW
**[HARPER_INBOUND.md](HARPER_INBOUND.md)** - First overview document
- Perfect for: Basic understanding of Harper's role
- Contains: Call flows, qualification criteria, objection handlers
- Read time: 15 minutes

---

## 🔍 Quick Navigation

### If you're...

**A caller (prospect):**
→ You'll get Harper's greeting and 5-step call flow

**Harold (decision-maker/closer):**
→ Read [HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md)
→ Reference [HARPER_QUICK_REFERENCE.md](HARPER_QUICK_REFERENCE.md) before calls
→ Study [HARPER_CONVERSATION_EXAMPLES.md](HARPER_CONVERSATION_EXAMPLES.md)

**A Harper operator:**
→ Start with [HARPER_QUICK_REFERENCE.md](HARPER_QUICK_REFERENCE.md)
→ Study [HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md)
→ Reference [HARPER_CONVERSATION_EXAMPLES.md](HARPER_CONVERSATION_EXAMPLES.md) for patterns

**A developer:**
→ Read [HARPER_SETUP_COMPLETE.md](HARPER_SETUP_COMPLETE.md)
→ Check `app.py` for system prompt (lines ~55-150)
→ See API endpoints: `/api/harper/inbound`, `/api/harper/greeting`

**A manager/operations:**
→ Read [HARPER_SETUP_COMPLETE.md](HARPER_SETUP_COMPLETE.md)
→ Track metrics in [HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md) (pages 35+)

---

## 🎯 Harper's 5-Step Call Flow

1. **IDENTIFY** (15 sec) - Get name & company
2. **UNDERSTAND** (20-30 sec) - Find their pain point
3. **CONNECT** (30-45 sec) - Match pain to ROI with numbers
4. **QUALIFY** (20 sec) - Budget authority? Timeline? Both YES?
5. **BOOK** (30 sec) - Get on Harold's calendar (Tues 10 AM or Thurs 2 PM ET)

**Total call time:** 5-10 minutes

---

## 💡 Industries Harper Can Talk To

Harper is trained on these 10 industries with specific ROI metrics:

1. **CONSTRUCTION** - Save 15-25 hrs/week, reduce delays 30%
2. **HVAC/PLUMBING/ELECTRICAL** - Book 20% more, reduce no-shows 40%
3. **RESTAURANTS** - Reduce waste 20-30%, optimize labor 15%
4. **TRUCKING/LOGISTICS** - Reduce fuel 8-15%, save 12-20 hrs/week
5. **MANUFACTURING** - Increase output 15-25%, reduce defects 30%
6. **AUTO REPAIR/BODY SHOPS** - Book 25% more, reduce delays 35%
7. **PROPERTY MANAGEMENT/JANITORIAL** - Reduce response 50%, automate billing 100%
8. **AGRICULTURE/FARMING** - Increase yield 10-15%, reduce downtime 25%
9. **WASTE MANAGEMENT** - Cut fuel 12-18%, reduce missed pickups 35%
10. **RETAIL/CONVENIENCE/GAS STATIONS** - Reduce stockouts 40%, optimize staffing 20%

For other industries: "Most businesses see 20-35% cost reduction and save 15-25 hours weekly with AI automation."

---

## 🛑 Objection Handling

Harper has specific responses for 7 common objections:

1. **"How much does this cost?"** → Lead with 60-90 day ROI, pivot to free discovery call
2. **"We're not ready for AI"** → Competitors are doing it, early movers win
3. **"I need to talk to my team"** → Have call with Harold first, bring real numbers
4. **"We tried automation before"** → This is different, built for your industry
5. **"Can you just send me info?"** → Call shows system, maps to business
6. **"We're too small"** → Smaller operations see ROI FASTER
7. **"I'm too busy"** → That's why you need this - busiest operators save most time

See [HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md) pages 31-45 for full responses.

---

## ✅ Qualification Criteria

Harper books a call if ALL are YES:
- ✅ Real operational pain point (not just curious)
- ✅ Budget authority OR can connect to decision-maker
- ✅ Timeline: Next 90 days
- ✅ Open to 30-minute discovery call

Any NO = Polite disqualification.

---

## 🔐 What Harper WILL Say

✅ "Yeah, that's exactly what Harold helps with"
✅ "Most [INDUSTRY] clients save [SPECIFIC ROI]"
✅ "Harold will show you exactly how it works"
✅ "Let me get you on Harold's calendar"
✅ "Fair enough?" / "Sound fair?" / "Make sense?"

## ❌ What Harper WON'T Say

❌ "We guarantee you'll save X hours"
❌ "No other company can do what we do"
❌ "You really need this right now"
❌ "I can answer that" (technical questions)
❌ Technical implementation details

---

## 📞 System Details

### Greeting
```
"Thanks for calling Trapier Management. I'm Harold's AI assistant Harper. How can I help you today?"
```

### Available Times to Book
- **Tuesday:** 10:00 AM Eastern
- **Thursday:** 2:00 PM Eastern
- **Duration:** 30 minutes
- **Format:** Zoom (link in calendar invite)

### API Endpoints
- `GET /api/harper/greeting` - Get Harper's greeting
- `POST /api/harper/inbound` - Setup Harper for inbound call

### Phone Number to Route
- **Trapier Management Phone:** +17047418085
- Route inbound calls to: `/api/harper/inbound` webhook

---

## 🎯 Success Metrics to Track

**Call Metrics:**
- Total inbound calls
- Average call duration
- Call completion rate

**Qualification Metrics:**
- % from target industries
- % with specific pain point
- % who booked discovery call
- % of booked calls that show up

**Lead Quality:**
- Which industries book most
- Average time-to-close
- ROI per lead source
- Conversion rate (Harper book → Harold close → Customer)

See [HARPER_OPERATING_MANUAL.md](HARPER_OPERATING_MANUAL.md) pages 35+ for detailed metrics.

---

## 🚀 Deployment

### Current Status
✅ System prompt in app.py
✅ API endpoints created
✅ Documentation complete
✅ Code committed to GitHub

### To Deploy
1. Deploy Harpoon to Railway
2. Configure Telnyx to route inbound → `/api/harper/inbound`
3. Test with a call to +17047418085
4. Start taking qualified inbound calls

### To Test Locally
```bash
# Get greeting
curl http://localhost:5000/api/harper/greeting

# Setup inbound
curl -X POST http://localhost:5000/api/harper/inbound \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test", "phone_number": "+19106248483"}'
```

---

## 📚 File Sizes & Read Times

| File | Size | Time | Purpose |
|------|------|------|---------|
| HARPER_QUICK_REFERENCE.md | 5.5K | 5 min | Quick lookup during calls |
| HARPER_OPERATING_MANUAL.md | 18K | 30 min | Complete training manual |
| HARPER_SETUP_COMPLETE.md | 9.4K | 15 min | Project overview |
| HARPER_CONVERSATION_EXAMPLES.md | 12K | 20 min | Real examples |
| HARPER_INBOUND.md | 12K | 15 min | Initial overview |

**Total Documentation:** 56.9K | 95 minutes to read all

---

## 🎖️ Harper Represents

- **Company:** Trapier Management LLC
- **Owner:** Harold Trapier (Service-Connected Disabled Veteran)
- **Service:** AI automation for traditional industries
- **Authority:** Book 30-minute discovery calls only
- **Tone:** Professional, direct, respectful, human

---

## 💬 Quick Reference

**Harper's objective:** Qualify good fits and book discovery calls

**NOT Harper's job:**
- Close deals (Harold does that)
- Provide pricing quotes (Harold does that)
- Answer technical questions (Harold does that)
- Make promises (Harold discusses realistic outcomes)

**Harper IS:**
- Professional gatekeeper
- Lead qualifier
- Call booker
- Representative of veteran-owned business

---

## 🔗 Internal Cross-References

**If you need to know about:**
- **5-step call flow** → All files, especially HARPER_QUICK_REFERENCE.md
- **Industry pain points** → HARPER_OPERATING_MANUAL.md pages 11-30
- **Objection handling** → HARPER_OPERATING_MANUAL.md pages 31-45
- **Real conversation flow** → HARPER_CONVERSATION_EXAMPLES.md
- **Deployment & testing** → HARPER_SETUP_COMPLETE.md
- **Voice & tone** → HARPER_OPERATING_MANUAL.md pages 46-50
- **System prompt** → app.py lines ~55-150

---

## ✨ Harper is Ready!

Harper is fully configured, documented, and ready to:
- ✅ Answer your phone professionally
- ✅ Qualify inbound leads by industry and pain point
- ✅ Connect pain points to specific ROI metrics
- ✅ Handle objections naturally
- ✅ Book discovery calls with Harold
- ✅ Represent Trapier Management with respect

**Deploy Harpoon to production and start taking qualified calls!**

---

**Last Updated:** December 30, 2025
**Status:** ✅ Complete and Ready for Deployment
**Author:** Harper - Trapier Management's AI Assistant

For questions or updates, contact Harold Trapier at info@trapiermanagement.com
