# Meta Ads Ultimate Dashboard — Complete Usage Book
# لوحة تحكم إعلانات ميتا الشاملة — كتاب الاستخدام الكامل

---

## Table of Contents / جدول المحتويات

1. [Introduction / المقدمة](#1-introduction--المقدمة)
2. [Installation / التثبيت](#2-installation--التثبيت)
3. [Getting Your Meta API Credentials / الحصول على بيانات اعتماد API](#3-getting-your-meta-api-credentials--الحصول-على-بيانات-اعتماد-api)
4. [Multi-Profile System / نظام الملفات الشخصية المتعددة](#4-multi-profile-system--نظام-الملفات-الشخصية-المتعددة)
5. [Data Extraction / استخراج البيانات](#5-data-extraction--استخراج-البيانات)
6. [Campaign Manager / مدير الحملات](#6-campaign-manager--مدير-الحملات)
7. [Ad Set Manager / مدير مجموعات الإعلانات](#7-ad-set-manager--مدير-مجموعات-الإعلانات)
8. [Ads Manager / مدير الإعلانات](#8-ads-manager--مدير-الإعلانات)
9. [Audience Manager / مدير الجماهير](#9-audience-manager--مدير-الجماهير)
10. [Budget Center / مركز الميزانية](#10-budget-center--مركز-الميزانية)
11. [Performance Monitor / مراقب الأداء](#11-performance-monitor--مراقب-الأداء)
12. [Rules Engine / محرك القواعد](#12-rules-engine--محرك-القواعد)
13. [A/B Testing / اختبارات A/B](#13-ab-testing--اختبارات-ab)
14. [Funnel & Attribution / القمع والإسناد](#14-funnel--attribution--القمع-والإسناد)
15. [Report Builder / مُنشئ التقارير](#15-report-builder--منشئ-التقارير)
16. [Activity Log / سجل النشاط](#16-activity-log--سجل-النشاط)
17. [Data Studio / استوديو البيانات](#17-data-studio--استوديو-البيانات)
18. [Settings / الإعدادات](#18-settings--الإعدادات)
19. [Power BI Integration / تكامل Power BI](#19-power-bi-integration--تكامل-power-bi)
20. [KPI Engine / محرك مؤشرات الأداء](#20-kpi-engine--محرك-مؤشرات-الأداء)
21. [Troubleshooting / حل المشكلات](#21-troubleshooting--حل-المشكلات)
22. [Best Practices / أفضل الممارسات](#22-best-practices--أفضل-الممارسات)
23. [API Reference / مرجع API](#23-api-reference--مرجع-api)
24. [Glossary / المصطلحات](#24-glossary--المصطلحات)

---

## 1. Introduction / المقدمة

### English

The Meta Ads Ultimate Dashboard is a **complete replacement** for Meta Ads Manager. It provides full CRUD (Create, Read, Update, Delete) operations for campaigns, ad sets, and ads via the Meta Marketing API v25.0. Built on Streamlit with a Windows 11-inspired UI, it offers 14+ pages covering every aspect of ad management.

**Key capabilities:**
- Full campaign lifecycle management (create, edit, pause, activate, duplicate, delete)
- Data extraction with parallel execution, pagination, and automatic chunking for large datasets
- 10 standard KPIs + custom formula engine with AST-based safe evaluation
- Power BI template generation with 35+ DAX measures
- Multi-profile system for managing multiple businesses/brands
- Automated rules engine (stop-loss, budget scaling, creative rotation)
- A/B testing framework with statistical significance calculation
- Export to CSV, JSON, Excel, and Google Sheets

### العربية

لوحة تحكم إعلانات ميتا الشاملة هي **بديل كامل** لمدير إعلانات ميتا. توفر عمليات CRUD كاملة (إنشاء، قراءة، تحديث، حذف) للحملات ومجموعات الإعلانات والإعلانات عبر Meta Marketing API الإصدار v25.0. مبنية على Streamlit بواجهة مستوحاة من Windows 11، وتقدم أكثر من 14 صفحة تغطي كل جانب من جوانب إدارة الإعلانات.

**القدرات الرئيسية:**
- إدارة دورة حياة الحملة الكاملة (إنشاء، تعديل، إيقاف مؤقت، تفعيل، نسخ، حذف)
- استخراج البيانات مع التنفيذ المتوازي والترقيم والتقسيم التلقائي للمجموعات الكبيرة
- 10 مؤشرات أداء قياسية + محرك صيغ مخصصة مع تقييم آمن قائم على AST
- إنشاء قوالب Power BI مع أكثر من 35 معادلة DAX
- نظام ملفات شخصية متعددة لإدارة عدة شركات/علامات تجارية
- محرك قواعد آلي (وقف الخسائر، توسيع الميزانية، تدوير الإبداعات)
- إطار اختبارات A/B مع حساب الأهمية الإحصائية
- تصدير إلى CSV، JSON، Excel، و Google Sheets

---

## 2. Installation / التثبيت

### English

#### Prerequisites
- **Python 3.10+** — Download from [python.org](https://www.python.org/downloads/)
- **Git** — Download from [git-scm.com](https://git-scm.com/downloads)
- **Meta Developer Account** — [developers.facebook.com](https://developers.facebook.com/)

#### Windows 11 Setup

```powershell
# 1. Clone the repository
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit
git checkout devin/1776967279-ultimate-dashboard

# 2. Run automated setup
.\scripts\setup.ps1

# 3. Edit .env with your credentials
notepad .env

# 4. Launch the dashboard
.\scripts\start-ultimate.bat
```

#### Mac/Linux Setup

```bash
# 1. Clone the repository
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit
git checkout devin/1776967279-ultimate-dashboard

# 2. Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
nano .env  # Add your META_ACCESS_TOKEN and META_AD_ACCOUNT_ID

# 4. Launch the dashboard
streamlit run app.py
```

The dashboard opens at **http://localhost:8501**.

### العربية

#### المتطلبات الأساسية
- **Python 3.10+** — تحميل من [python.org](https://www.python.org/downloads/)
- **Git** — تحميل من [git-scm.com](https://git-scm.com/downloads)
- **حساب مطور ميتا** — [developers.facebook.com](https://developers.facebook.com/)

#### إعداد Windows 11

```powershell
# 1. استنساخ المستودع
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit
git checkout devin/1776967279-ultimate-dashboard

# 2. تشغيل الإعداد التلقائي
.\scripts\setup.ps1

# 3. تعديل ملف .env بالبيانات الخاصة بك
notepad .env

# 4. تشغيل لوحة التحكم
.\scripts\start-ultimate.bat
```

#### إعداد Mac/Linux

```bash
# 1. استنساخ المستودع
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit
git checkout devin/1776967279-ultimate-dashboard

# 2. إنشاء بيئة افتراضية وتثبيت
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. تكوين البيانات
cp .env.example .env
nano .env  # أضف META_ACCESS_TOKEN و META_AD_ACCOUNT_ID

# 4. تشغيل لوحة التحكم
streamlit run app.py
```

لوحة التحكم تفتح على **http://localhost:8501**.

---

## 3. Getting Your Meta API Credentials / الحصول على بيانات اعتماد API

### English

#### Step 1: Create a Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Name your app (e.g., "My Ads Dashboard")
5. Complete the setup

#### Step 2: Get Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click "Generate Access Token"
4. Grant these permissions:
   - `ads_read` — Read ad account data
   - `ads_management` — Create/edit/delete campaigns
   - `business_management` — Access business accounts
   - `read_insights` — Read performance data
5. Copy the token — this is your `META_ACCESS_TOKEN`

**Important:** The default token expires in ~1 hour. For production use:
1. Go to your app Settings → Basic
2. Note the App ID and App Secret
3. Exchange for a long-lived token (60 days):
```
https://graph.facebook.com/v25.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id={APP_ID}&
  client_secret={APP_SECRET}&
  fb_exchange_token={SHORT_LIVED_TOKEN}
```

#### Step 3: Get Ad Account ID

1. Go to [Meta Ads Manager](https://www.facebook.com/adsmanager/)
2. Look at the URL — it contains `act_XXXXXXXXX`
3. Or go to Business Settings → Accounts → Ad Accounts
4. Copy the full ID including the `act_` prefix

#### Step 4: Configure .env

```
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxx
META_AD_ACCOUNT_ID=act_123456789
META_API_VERSION=v25.0
```

### العربية

#### الخطوة 1: إنشاء تطبيق ميتا

1. اذهب إلى [developers.facebook.com](https://developers.facebook.com/)
2. انقر "تطبيقاتي" ← "إنشاء تطبيق"
3. اختر نوع "أعمال"
4. سمِّ تطبيقك (مثلاً "لوحة تحكم إعلاناتي")
5. أكمل الإعداد

#### الخطوة 2: الحصول على رمز الوصول

1. اذهب إلى [مستكشف Graph API](https://developers.facebook.com/tools/explorer/)
2. اختر تطبيقك من القائمة المنسدلة
3. انقر "إنشاء رمز وصول"
4. امنح هذه الأذونات:
   - `ads_read` — قراءة بيانات حساب الإعلانات
   - `ads_management` — إنشاء/تعديل/حذف الحملات
   - `business_management` — الوصول إلى حسابات الأعمال
   - `read_insights` — قراءة بيانات الأداء
5. انسخ الرمز — هذا هو `META_ACCESS_TOKEN` الخاص بك

**مهم:** الرمز الافتراضي تنتهي صلاحيته خلال ~ساعة واحدة. للاستخدام الإنتاجي:
1. اذهب إلى إعدادات تطبيقك ← أساسي
2. دوِّن معرف التطبيق وسر التطبيق
3. استبدل برمز طويل الأمد (60 يوم)

#### الخطوة 3: الحصول على معرف حساب الإعلانات

1. اذهب إلى [مدير إعلانات ميتا](https://www.facebook.com/adsmanager/)
2. انظر إلى الرابط — يحتوي على `act_XXXXXXXXX`
3. أو اذهب إلى إعدادات الأعمال ← الحسابات ← حسابات الإعلانات
4. انسخ المعرف الكامل بما في ذلك البادئة `act_`

---

## 4. Multi-Profile System / نظام الملفات الشخصية المتعددة

### English

The Profile Manager allows you to manage multiple businesses and brands from a single dashboard.

#### Creating a Profile

1. Navigate to **Profile Manager** page (page 14 in sidebar)
2. Click the **Create Profile** tab
3. Fill in:
   - **Profile Name** — e.g., "Nike US" or "My E-Commerce Store"
   - **Business Name** — Legal entity name
   - **Industry** — Select from 16+ industry categories
   - **Brand Color** — Choose from 10 preset colors for visual identification
   - **Access Token** — Your Meta API token for this account
   - **Ad Account ID** — The `act_XXXXXXXXX` for this account
   - **Currency** — USD, EUR, GBP, SAR, EGP, etc.
   - **Timezone** — Your account's timezone
   - **Monthly Budget** — Total monthly ad spend budget
   - **Tags** — Comma-separated tags for organization
4. Set **Performance Benchmarks**:
   - Target CTR (%), Target ROAS, Max Frequency
   - Max CPA ($), Bleeder CTR threshold, Bleeder spend threshold
5. Click **Create Profile**

#### Switching Profiles

- Use the **brand switcher dropdown** at the top of the sidebar
- The color-coded card shows the active profile name and business
- Switching instantly loads that profile's credentials and settings
- Previous workspace state (last page, date preset, etc.) is restored

#### Exporting & Importing Profiles

**Export:**
1. Go to Profile Manager → Import/Export tab
2. Select profiles to export
3. Click **Generate Export** → Download JSON
4. Credentials are automatically excluded for security

**Import:**
1. Upload a previously exported JSON file
2. Choose whether to overwrite existing profiles with matching IDs
3. Click **Import Profiles**
4. Re-enter credentials for imported profiles

### العربية

يتيح لك مدير الملفات الشخصية إدارة عدة شركات وعلامات تجارية من لوحة تحكم واحدة.

#### إنشاء ملف شخصي

1. انتقل إلى صفحة **مدير الملفات الشخصية** (الصفحة 14 في الشريط الجانبي)
2. انقر على علامة التبويب **إنشاء ملف شخصي**
3. املأ:
   - **اسم الملف الشخصي** — مثلاً "نايكي الولايات المتحدة" أو "متجري الإلكتروني"
   - **اسم الشركة** — اسم الكيان القانوني
   - **الصناعة** — اختر من أكثر من 16 فئة صناعية
   - **لون العلامة التجارية** — اختر من 10 ألوان مُعدة مسبقاً
   - **رمز الوصول** — رمز Meta API لهذا الحساب
   - **معرف حساب الإعلانات** — الـ `act_XXXXXXXXX` لهذا الحساب
   - **العملة** — USD، EUR، GBP، SAR، EGP، إلخ
   - **المنطقة الزمنية** — المنطقة الزمنية لحسابك
   - **الميزانية الشهرية** — إجمالي ميزانية الإنفاق الإعلاني الشهري
   - **الوسوم** — وسوم مفصولة بفواصل للتنظيم
4. اضبط **معايير الأداء**
5. انقر **إنشاء ملف شخصي**

#### تبديل الملفات الشخصية

- استخدم **قائمة تبديل العلامات التجارية** في أعلى الشريط الجانبي
- البطاقة الملونة تعرض اسم الملف النشط والشركة
- التبديل يحمّل فوراً بيانات اعتماد ذلك الملف وإعداداته
- يتم استعادة حالة مساحة العمل السابقة

---

## 5. Data Extraction / استخراج البيانات

### English

The extraction engine is the core of the dashboard. It pulls data from the Meta Marketing API with automatic error handling.

#### Basic Extraction

1. **Connect** — Enter your token and account ID in the sidebar, click Connect
2. **Select Date Range** — Choose a preset (last_7d, last_30d, etc.) or custom dates
3. **Select Levels** — Account, Campaign, Ad Set, Ad (can select multiple)
4. **Select Breakdowns** — None, Age, Gender, Country, Platform, etc.
5. **Click START EXTRACTION**

#### Date Range Options

| Preset | Period | API Value |
|--------|--------|-----------|
| Today | Current day | `today` |
| Yesterday | Previous day | `yesterday` |
| Last 3 Days | 3 days ago → yesterday | `last_3d` |
| Last 7 Days | 7 days ago → yesterday | `last_7d` |
| Last 14 Days | 14 days ago → yesterday | `last_14d` |
| Last 28 Days | 28 days ago → yesterday | `last_28d` |
| Last 30 Days | 30 days ago → yesterday | `last_30d` |
| Last 60 Days | 60 days ago → yesterday | `last_60d` |
| Last 90 Days | 90 days ago → yesterday | `last_90d` |
| This Month | 1st of month → today | `this_month` |
| Last Month | Previous full month | `last_month` |
| This Quarter | Start of quarter → today | `this_quarter` |
| This Year | Jan 1 → today | `this_year` |
| Last Year | Previous full year | `last_year` |
| Lifetime | All time | `maximum` |
| **Custom Range** | Any start/end dates you pick | `time_range` |

#### Handling Large Requests

The system has a **3-tier fallback** for handling "request too large" errors:

1. **Direct Query** — Tries the request as-is
2. **Chunked Fetch** — If too large, automatically splits the date range into 7-day chunks and fetches each separately, then merges the results
3. **Async Report** — If chunks still fail, uses Meta's asynchronous reporting endpoint (POST to create report job, poll for completion, then download)

This means you can request **any date range** (30 days, 90 days, even a full year) and the system will find a way to get the data.

#### Breakdowns

| Key | Description | API Fields |
|-----|-------------|------------|
| None | No breakdown | — |
| Age | By age range | `age` |
| Gender | By gender | `gender` |
| Age + Gender | Combined | `age, gender` |
| Country | By country | `country` |
| Region | By state/region | `region` |
| DMA | By DMA region | `dma` |
| Platform | Facebook/Instagram/etc. | `publisher_platform` |
| Device | Mobile/Desktop/Tablet | `device_platform` |
| Placement | Feed/Stories/Reels/etc. | `platform_position` |
| Impression Device | iOS/Android/Desktop | `impression_device` |
| Product ID | For catalog ads | `product_id` |
| Hourly (Advertiser) | By hour | `hourly_stats_aggregated_by_advertiser_time_zone` |
| Hourly (Audience) | By hour (audience TZ) | `hourly_stats_aggregated_by_audience_time_zone` |

#### Output Files

Every extraction creates:
- `raw/` — Individual CSV and JSON files per level+breakdown combination
- `entities/` — Account info, campaigns, ad sets, ads listings
- `powerbi/` — Power Query M code + DAX suggestions
- `MASTER_ALL_DATA.xlsx` — All data in one Excel workbook
- `MASTER_ALL_DATA.json` — All data in one JSON file
- `manifest.json` — Extraction metadata and file listing

### العربية

محرك الاستخراج هو جوهر لوحة التحكم. يسحب البيانات من Meta Marketing API مع معالجة الأخطاء التلقائية.

#### الاستخراج الأساسي

1. **الاتصال** — أدخل الرمز ومعرف الحساب في الشريط الجانبي، انقر اتصال
2. **اختيار نطاق التاريخ** — اختر إعداداً مسبقاً أو تواريخ مخصصة
3. **اختيار المستويات** — حساب، حملة، مجموعة إعلانات، إعلان
4. **اختيار التقسيمات** — بلا، عمر، جنس، بلد، منصة، إلخ
5. **انقر ابدأ الاستخراج**

#### التعامل مع الطلبات الكبيرة

يحتوي النظام على **نظام احتياطي ثلاثي المستويات** للتعامل مع أخطاء "الطلب كبير جداً":

1. **استعلام مباشر** — يجرب الطلب كما هو
2. **جلب مقسم** — إذا كان كبيراً جداً، يقسم تلقائياً نطاق التاريخ إلى أجزاء من 7 أيام
3. **تقرير غير متزامن** — إذا فشلت الأجزاء، يستخدم نقطة نهاية التقارير غير المتزامنة

---

## 6. Campaign Manager / مدير الحملات

### English

Full campaign lifecycle management — the most important page.

#### All Campaigns Tab

- **Filters**: Status (Active, Paused, Deleted, Archived), Objective, Search by name
- **Metrics shown**: Total campaigns, Active count, Paused count
- **Columns**: ID, Name, Status, Objective, Daily Budget, Lifetime Budget, Budget Remaining, Bid Strategy, Created, Updated
- **Inline Actions** (select campaigns first):
  - **Activate** — Set status to ACTIVE (starts serving)
  - **Pause** — Set status to PAUSED (stops serving)
  - **Duplicate** — Create a copy of the campaign
  - **Delete** — Permanently remove
  - **Update Budget** — Change daily budget for selected campaigns (minimum $1)

#### Create Campaign Tab

| Field | Required | Description |
|-------|----------|-------------|
| Campaign Name | Yes | Display name for the campaign |
| Objective | Yes | CONVERSIONS, TRAFFIC, AWARENESS, ENGAGEMENT, LEADS, APP_INSTALLS, VIDEO_VIEWS, REACH, MESSAGES, CATALOG_SALES, STORE_TRAFFIC |
| Bid Strategy | No | LOWEST_COST_WITHOUT_CAP, LOWEST_COST_WITH_BID_CAP, COST_CAP, MINIMUM_ROAS |
| Daily Budget ($) | No | Per-day spend limit |
| Lifetime Budget ($) | No | Total spend limit for campaign lifetime |
| Special Ad Categories | No | CREDIT, EMPLOYMENT, HOUSING, SOCIAL_ISSUES_ELECTIONS_POLITICS |
| Initial Status | Yes | PAUSED (recommended) or ACTIVE |

#### Deep Insights Tab

- View performance data for any campaign
- Date range selection
- Metrics: Spend, Impressions, Clicks, CTR, CPC, CPA, ROAS, Conversions
- Day-by-day trend charts

#### Compare Tab

- Compare 2-5 campaigns side by side
- See which campaign performs best on each metric
- Automatic winner highlighting

### العربية

إدارة دورة حياة الحملة الكاملة — الصفحة الأكثر أهمية.

#### علامة تبويب جميع الحملات

- **الفلاتر**: الحالة (نشط، متوقف مؤقتاً، محذوف، مؤرشف)، الهدف، بحث بالاسم
- **المقاييس المعروضة**: إجمالي الحملات، العدد النشط، العدد المتوقف
- **الإجراءات المباشرة** (اختر الحملات أولاً):
  - **تفعيل** — تعيين الحالة إلى نشط (يبدأ العرض)
  - **إيقاف مؤقت** — تعيين الحالة إلى متوقف (يوقف العرض)
  - **نسخ** — إنشاء نسخة من الحملة
  - **حذف** — إزالة نهائية
  - **تحديث الميزانية** — تغيير الميزانية اليومية (الحد الأدنى $1)

#### إنشاء حملة

| الحقل | مطلوب | الوصف |
|-------|-------|-------|
| اسم الحملة | نعم | الاسم المعروض للحملة |
| الهدف | نعم | تحويلات، زيارات، وعي، تفاعل، عملاء محتملون، إلخ |
| استراتيجية المزايدة | لا | أقل تكلفة، حد أقصى للمزايدة، حد تكلفة، حد أدنى للعائد |
| الميزانية اليومية | لا | حد الإنفاق اليومي |
| الميزانية الإجمالية | لا | حد الإنفاق الكلي لعمر الحملة |
| فئات إعلانية خاصة | لا | ائتمان، توظيف، إسكان، قضايا اجتماعية |

---

## 7. Ad Set Manager / مدير مجموعات الإعلانات

### English

#### Creating an Ad Set

Required fields:
- **Campaign ID** — The campaign to create the ad set under
- **Ad Set Name** — Display name
- **Optimization Goal** — What to optimize for: LINK_CLICKS, OFFSITE_CONVERSIONS, IMPRESSIONS, REACH, LANDING_PAGE_VIEWS, etc. (25+ options)
- **Billing Event** — When you get charged: IMPRESSIONS, LINK_CLICKS, THRUPLAY
- **Daily Budget** — Minimum $1/day

Targeting options:
- **Age Range** — 13 to 65 (sliders)
- **Genders** — All, Male, Female
- **Countries** — Comma-separated country codes (US, UK, EG, SA, AE, etc.)
- **Interests** — JSON array of interest objects from the targeting browser
- **Schedule** — Start date and optional end date
- **Dayparting** — 24x7 hour-by-day grid for ad scheduling

#### Targeting Builder

1. Set your demographic criteria (age, gender, location)
2. Use **Search Interests** to find targeting options
3. The system searches Meta's targeting catalog and shows:
   - Interest name
   - Audience size
   - Interest ID (needed for targeting spec)
4. Copy the targeting JSON to use in ad set creation

### العربية

#### إنشاء مجموعة إعلانات

الحقول المطلوبة:
- **معرف الحملة** — الحملة لإنشاء المجموعة تحتها
- **اسم المجموعة** — الاسم المعروض
- **هدف التحسين** — ما يجب تحسينه: نقرات الرابط، تحويلات خارج الموقع، مرات الظهور، الوصول، إلخ
- **حدث الفوترة** — متى يتم تحصيل الرسوم: مرات الظهور، نقرات الرابط
- **الميزانية اليومية** — الحد الأدنى $1/يوم

خيارات الاستهداف:
- **نطاق العمر** — 13 إلى 65
- **الجنس** — الكل، ذكر، أنثى
- **البلدان** — رموز البلدان مفصولة بفواصل
- **الاهتمامات** — مصفوفة JSON من كائنات الاهتمام

---

## 8. Ads Manager / مدير الإعلانات

### English

#### Ad Creation

1. Select the **Ad Set ID** the ad belongs to
2. Enter the **Ad Name**
3. Provide the **Creative** — either:
   - An existing **Creative ID** from your account
   - Or create a new creative with:
     - Page ID (your Facebook Page)
     - Link URL (landing page)
     - Message (ad text)
     - Image URL or Image Hash (from uploaded image)
4. Set initial status (PAUSED recommended)
5. Click **Create Ad**

#### Creative Library

- View all creatives in your account
- See thumbnail previews
- Copy creative IDs for reuse
- Filter by date created

### العربية

#### إنشاء الإعلانات

1. اختر **معرف مجموعة الإعلانات** التي ينتمي إليها الإعلان
2. أدخل **اسم الإعلان**
3. قدّم **الإبداع** — إما:
   - **معرف إبداع** موجود من حسابك
   - أو إنشاء إبداع جديد مع: معرف الصفحة، رابط URL، الرسالة، صورة
4. اضبط الحالة الأولية (متوقف مؤقتاً مُوصى به)
5. انقر **إنشاء إعلان**

---

## 9. Audience Manager / مدير الجماهير

### English

#### Custom Audiences

Create audiences from:
- **Customer Lists** — Upload email/phone lists for matching
- **Website Visitors** — Pixel-based retargeting
- **App Activity** — Users who performed in-app actions
- **Engagement** — People who interacted with your content

#### Lookalike Audiences

- Select a **source audience** (custom audience)
- Choose the **country** for the lookalike
- Set the **percentage** (1% = most similar, 10% = largest reach)
- Larger percentages give more reach but less similarity

#### Saved Audiences

- Save targeting configurations for reuse
- Include demographics, interests, behaviors, locations
- Apply saved audiences quickly to new ad sets

### العربية

#### الجماهير المخصصة

إنشاء جماهير من:
- **قوائم العملاء** — رفع قوائم البريد الإلكتروني/الهاتف
- **زوار الموقع** — إعادة الاستهداف القائمة على البكسل
- **نشاط التطبيق** — المستخدمون الذين أجروا إجراءات داخل التطبيق
- **التفاعل** — الأشخاص الذين تفاعلوا مع محتواك

#### الجماهير المشابهة

- اختر **جمهور مصدر** (جمهور مخصص)
- اختر **البلد** للجمهور المشابه
- اضبط **النسبة المئوية** (1% = الأكثر تشابهاً، 10% = الأكبر وصولاً)

---

## 10. Budget Center / مركز الميزانية

### English

#### Budget Allocation Methods

1. **Equal Split** — Divides total budget equally among selected campaigns
2. **Custom Weights** — Assign percentage weights to each campaign, budget distributed proportionally
3. **Performance-Based** — Requires historical extraction data; allocates more to better-performing campaigns

#### Spend Pacing

- Track daily spend vs. budget
- See pacing charts (on-track, under-pacing, over-pacing)
- Forecast remaining budget for the period

#### Budget Forecast

- Input total budget and campaign count
- See recommended daily budgets
- View estimated reach and results based on historical CPM/CPC

### العربية

#### طرق تخصيص الميزانية

1. **تقسيم متساوٍ** — يقسم الميزانية الإجمالية بالتساوي بين الحملات المختارة
2. **أوزان مخصصة** — تعيين نسب مئوية لكل حملة، يتم توزيع الميزانية بشكل متناسب
3. **قائم على الأداء** — يتطلب بيانات استخراج تاريخية، يخصص المزيد للحملات الأفضل أداءً

---

## 11. Performance Monitor / مراقب الأداء

### English

#### Bleeder Detection

Identifies ads **wasting money** based on your benchmarks:
- CTR below threshold (default: 1%)
- Spend above threshold (default: $10)
- High frequency (default: > 3.5)
- These thresholds are customizable per profile

#### Creative Fatigue Detection

Monitors for declining CTR over time, which indicates ad fatigue:
- Compares current vs. previous period CTR
- Flags when CTR drops > 20% over 3 days

#### Health Score

Each campaign/ad set/ad gets a health score (0-100):
- CTR performance vs. benchmark: 30 points
- Frequency vs. max: 20 points
- CPC vs. average: 20 points
- ROAS vs. target: 30 points

#### Anomaly Detection

Flags unusual spikes or drops:
- Spend suddenly 3x higher than average
- CTR drops by more than 50%
- Impressions go to zero unexpectedly

### العربية

#### كشف الهدر

يحدد الإعلانات **التي تهدر المال** بناءً على معاييرك:
- نسبة النقر إلى الظهور أقل من الحد (افتراضي: 1%)
- الإنفاق أعلى من الحد (افتراضي: $10)
- التكرار مرتفع (افتراضي: > 3.5)

#### كشف إرهاق الإبداع

يراقب انخفاض نسبة النقر بمرور الوقت

#### نقاط الصحة

كل حملة/مجموعة/إعلان يحصل على نقاط صحة (0-100)

---

## 12. Rules Engine / محرك القواعد

### English

Create automated rules that run periodically:

#### Available Rule Templates

1. **Stop Loss** — Pause ads when CPA exceeds threshold
2. **Budget Scaling** — Increase budget when ROAS exceeds target
3. **Creative Rotation** — Pause fatigued creatives (high frequency, low CTR)
4. **Budget Pacing** — Reduce budget when spend pacing too high
5. **Winner Scaling** — Increase budget for winning ad sets
6. **Night Pause** — Pause ads during non-converting hours

#### Creating a Rule

1. Select a template or create custom
2. Define **trigger condition** (metric + operator + value)
3. Set **action** (pause, activate, increase budget %, decrease budget %)
4. Set **frequency** (every 1h, 6h, 12h, 24h)
5. Set **notification** preference (in-app, email)

### العربية

إنشاء قواعد آلية تعمل بشكل دوري:

#### قوالب القواعد المتاحة

1. **وقف الخسائر** — إيقاف الإعلانات عندما يتجاوز CPA الحد
2. **توسيع الميزانية** — زيادة الميزانية عندما يتجاوز ROAS الهدف
3. **تدوير الإبداعات** — إيقاف الإبداعات المنهكة
4. **ضبط الإنفاق** — تقليل الميزانية عندما يكون الإنفاق مفرطاً
5. **توسيع الفائزين** — زيادة ميزانية المجموعات الفائزة
6. **إيقاف ليلي** — إيقاف الإعلانات خلال الساعات غير المحولة

---

## 13. A/B Testing / اختبارات A/B

### English

#### Setting Up a Test

1. **Test Name** — Descriptive name for the experiment
2. **Hypothesis** — What you're testing (e.g., "Blue CTA button increases CVR by 15%")
3. **Test Type** — Ad Creative, Ad Copy, Audience, Placement, Bid Strategy, Landing Page
4. **Primary Metric** — CTR, CPC, CPA, ROAS, CVR, CPM
5. **Variants** — Configure 2-5 variants with entity IDs (campaign/adset/ad IDs)
6. **Confidence Level** — 90%, 95%, 99%
7. **Duration** — 3 to 90 days

#### Sample Size Calculator

Input:
- **Baseline Rate** — Current conversion rate (e.g., 3%)
- **Minimum Detectable Effect** — Smallest improvement to detect (e.g., 10%)
- **Confidence Level** — 90%, 95%, 99%
- **Statistical Power** — 80%, 90%

Output:
- Required sample size per variant
- Estimated test duration based on your traffic

#### Statistical Significance

Uses the **two-proportion z-test**:
- Calculates z-score and p-value
- Declares winner when p-value < alpha (based on confidence level)
- Shows confidence interval for the difference

### العربية

#### إعداد اختبار

1. **اسم الاختبار** — اسم وصفي للتجربة
2. **الفرضية** — ما تختبره
3. **نوع الاختبار** — إبداع إعلاني، نص إعلاني، جمهور، موضع، استراتيجية مزايدة
4. **المقياس الأساسي** — CTR، CPC، CPA، ROAS، CVR، CPM
5. **المتغيرات** — تكوين 2-5 متغيرات مع معرفات الكيانات
6. **مستوى الثقة** — 90%، 95%، 99%
7. **المدة** — 3 إلى 90 يوم

#### حاسبة حجم العينة

- معدل الأساس الحالي
- أصغر تأثير قابل للكشف
- مستوى الثقة والقوة الإحصائية

---

## 14. Funnel & Attribution / القمع والإسناد

### English

#### Conversion Funnel

Visualizes the customer journey:
1. **Impressions** → How many people saw your ad
2. **Clicks** → How many clicked through
3. **Conversions** → How many completed the desired action
4. **Purchases** → How many bought

**Note:** If conversion/purchase data isn't available from your account, the system shows estimated values based on industry averages (3% click-to-conversion, 40% conversion-to-purchase) with a clear warning.

#### Attribution Models

- **Last Click** — 100% credit to last touchpoint
- **First Click** — 100% credit to first touchpoint
- **Linear** — Equal credit across all touchpoints
- **Time Decay** — More credit to recent touchpoints

### العربية

#### قمع التحويل

يصور رحلة العميل:
1. **مرات الظهور** ← كم شخص رأى إعلانك
2. **النقرات** ← كم نقر عليه
3. **التحويلات** ← كم أكمل الإجراء المطلوب
4. **المشتريات** ← كم اشترى

---

## 15. Report Builder / مُنشئ التقارير

### English

Create custom reports with any combination of:
- **Metrics** — 70+ available metrics across 6 categories
- **Breakdowns** — 14 breakdown types
- **Date Ranges** — Any preset or custom range
- **Levels** — Account, Campaign, Ad Set, Ad
- **Filters** — By campaign IDs, status, objective

Report templates:
- **Executive Summary** — High-level KPIs and trends
- **Campaign Performance** — Detailed per-campaign metrics
- **Creative Analysis** — Ad-level performance comparison
- **Audience Insights** — Demographic breakdown analysis
- **Budget Efficiency** — Spend optimization report

### العربية

إنشاء تقارير مخصصة مع أي مجموعة من:
- **المقاييس** — أكثر من 70 مقياس متاح عبر 6 فئات
- **التقسيمات** — 14 نوع تقسيم
- **نطاقات التاريخ** — أي إعداد مسبق أو نطاق مخصص
- **المستويات** — حساب، حملة، مجموعة إعلانات، إعلان

---

## 16. Activity Log / سجل النشاط

### English

Complete audit trail of all actions in your account:
- Campaign/ad set/ad creation, modification, deletion
- Status changes (active ↔ paused)
- Budget changes
- Timestamps for every action
- User who performed the action

### العربية

سجل تدقيق كامل لجميع الإجراءات في حسابك:
- إنشاء/تعديل/حذف الحملات ومجموعات الإعلانات والإعلانات
- تغييرات الحالة (نشط ↔ متوقف مؤقتاً)
- تغييرات الميزانية
- طوابع زمنية لكل إجراء

---

## 17. Data Studio / استوديو البيانات

### English

#### Pivot Tables

- Select any dataset from your extractions or upload a CSV
- Choose rows, columns, values, and aggregation (sum, mean, count, min, max)
- Interactive pivot table display

#### Charts

- Line charts, bar charts, scatter plots
- Choose X-axis, Y-axis, and color dimensions
- Export charts as images

#### Formula Lab

Create custom formulas using your data columns:
- Uses the safe AST-based formula engine
- Available functions: `abs`, `min`, `max`, `round`, `sqrt`, `log`, `log10`, `pow`
- Test formulas with sample data before applying
- Apply formulas to entire datasets

#### Period Comparison

Compare two time periods side by side:
- Current vs. Previous period
- Month-over-month
- Year-over-year
- See absolute and percentage differences

### العربية

#### الجداول المحورية

- اختر أي مجموعة بيانات من استخراجاتك أو ارفع ملف CSV
- اختر الصفوف والأعمدة والقيم والتجميع

#### الرسوم البيانية

- رسوم خطية، عمودية، نقطية
- اختر المحور السيني والمحور الصادي وبُعد اللون

#### معمل الصيغ

إنشاء صيغ مخصصة باستخدام أعمدة بياناتك:
- يستخدم محرك صيغ آمن قائم على AST
- الدوال المتاحة: `abs`، `min`، `max`، `round`، `sqrt`، `log`، `log10`، `pow`

---

## 18. Settings / الإعدادات

### English

View and manage system configuration:
- API Version (v25.0)
- Rate Limit (180 calls/hour)
- Max Retries (6)
- Cache TTL (300 seconds)
- Available KPIs and their formulas
- Available breakdowns and their API fields
- All 70+ metric fields grouped by category

### العربية

عرض وإدارة تكوين النظام:
- إصدار API (v25.0)
- حد المعدل (180 طلب/ساعة)
- الحد الأقصى لإعادة المحاولة (6)
- مدة صلاحية الذاكرة المؤقتة (300 ثانية)
- مؤشرات الأداء المتاحة وصيغها
- التقسيمات المتاحة وحقول API الخاصة بها

---

## 19. Power BI Integration / تكامل Power BI

### English

#### Generating a Template

1. Go to the **Power BI** tab in the main dashboard
2. Set the output directory and data folder path
3. Click **Generate Power BI Template**
4. The system creates:
   - **Star Schema** — 6 tables (Fact_Performance, Dim_Campaign, Dim_AdSet, Dim_Ad, Dim_Date, Dim_Location)
   - **35+ DAX Measures** — ROAS, CPA, CTR, CPM, CPC, CVR, AOV, Frequency, MoM changes, rolling averages
   - **7 Report Pages** — Executive Summary, Campaign Deep Dive, Creative Analysis, Audience Insights, Time Analysis, Funnel, Budget
   - **Power Query M Code** — For automated data refresh from CSV folder
   - **Theme JSON** — Windows 11-inspired colors and fonts

#### Loading into Power BI Desktop

1. Open Power BI Desktop
2. Get Data → Folder → Select your extraction output folder
3. Paste the Power Query M code from `power_query_folder_import.m`
4. Create measures by pasting DAX from `dax_measures.dax`
5. Apply theme from `theme.json`
6. Build reports using the layout definitions in `report_pages.json`

### العربية

#### إنشاء قالب

1. اذهب إلى علامة تبويب **Power BI** في لوحة التحكم الرئيسية
2. اضبط مجلد الإخراج ومسار مجلد البيانات
3. انقر **إنشاء قالب Power BI**
4. ينشئ النظام:
   - **مخطط نجمي** — 6 جداول
   - **أكثر من 35 معادلة DAX**
   - **7 صفحات تقارير**
   - **كود Power Query M**
   - **ملف السمة JSON**

---

## 20. KPI Engine / محرك مؤشرات الأداء

### English

#### Standard KPIs (10)

| KPI | Formula | Unit |
|-----|---------|------|
| **ROAS** | revenue / spend | ratio |
| **CPA** | spend / conversions | $ |
| **CTR** | clicks / impressions * 100 | % |
| **CPC** | spend / clicks | $ |
| **CPM** | (spend / impressions) * 1000 | $ |
| **CVR** | conversions / clicks * 100 | % |
| **AOV** | revenue / purchases | $ |
| **Frequency** | impressions / reach | ratio |
| **CPL** | spend / leads | $ |
| **ThruPlay Rate** | thruplay / impressions * 100 | % |

#### Custom KPIs

Each profile can define custom KPI formulas:
- Use any column name from your data
- Arithmetic operators: +, -, *, /, //, %, **
- Functions: abs, min, max, round, sqrt, log, log10, pow
- Example: `(revenue - spend) / spend * 100` for profit margin %

### العربية

#### مؤشرات الأداء القياسية (10)

| المؤشر | الصيغة | الوحدة |
|--------|--------|--------|
| **ROAS** | الإيرادات / الإنفاق | نسبة |
| **CPA** | الإنفاق / التحويلات | $ |
| **CTR** | النقرات / مرات الظهور * 100 | % |
| **CPC** | الإنفاق / النقرات | $ |
| **CPM** | (الإنفاق / مرات الظهور) * 1000 | $ |
| **CVR** | التحويلات / النقرات * 100 | % |
| **AOV** | الإيرادات / المشتريات | $ |
| **التكرار** | مرات الظهور / الوصول | نسبة |
| **CPL** | الإنفاق / العملاء المحتملون | $ |
| **معدل ThruPlay** | thruplay / مرات الظهور * 100 | % |

---

## 21. Troubleshooting / حل المشكلات

### English

#### "Request Too Large" Error

**Problem:** Meta API returns "Please reduce the amount of data you're asking for"

**Solution:** The system automatically handles this with 3-tier fallback:
1. Splits your date range into 7-day chunks
2. If still too large, splits into single-day chunks
3. If still failing, uses async reporting

**Manual workaround:** Use a shorter date range or fewer breakdowns.

#### No Data Returned for 30-Day Range

**Problem:** 30-day extraction returns empty but 7-day works

**Possible causes:**
1. **Token permissions** — Ensure `ads_read` and `read_insights` permissions
2. **Date range has no data** — New account may not have 30 days of history
3. **Too many metrics** — Try "Delivery" metrics only instead of "All"
4. **Breakdown incompatibility** — Some breakdowns don't work with certain levels

**Solution:** The chunked fetch system now handles this automatically. If 30 days is too much data, it fetches in 7-day chunks and merges.

#### Token Expired

**Problem:** "Token invalid" error

**Solution:**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Generate a new token
3. Update `.env` or your profile's access token
4. Reconnect in the sidebar

**For long-lived tokens:** Exchange for a 60-day token using the token exchange endpoint (see Section 3).

#### Rate Limiting

**Problem:** "Too many calls" error

**Solution:** The system automatically:
1. Monitors the `x-ad-account-usage` header
2. Slows down when usage exceeds 75%
3. Uses exponential backoff (3s, 6s, 12s, 24s, 48s, 96s) for rate limit errors
4. Maximum wait: 180 seconds per retry

#### Connection Failed

**Problem:** Cannot connect to Meta API

**Check:**
1. Internet connection
2. Token is not expired
3. Account ID includes `act_` prefix
4. No trailing whitespace in credentials
5. API version (v25.0) is current

#### Missing Metrics in Output

**Problem:** Some columns are missing from exported data

**Explanation:** Meta API only returns metrics that have data. If no video ads are running, video metrics will be absent. This is normal behavior.

### العربية

#### خطأ "الطلب كبير جداً"

**المشكلة:** API ميتا يعيد "يرجى تقليل كمية البيانات المطلوبة"

**الحل:** النظام يتعامل تلقائياً مع هذا عبر نظام احتياطي ثلاثي:
1. يقسم نطاق التاريخ إلى أجزاء من 7 أيام
2. إذا كان لا يزال كبيراً، يقسم إلى أجزاء يومية
3. إذا فشل، يستخدم التقارير غير المتزامنة

#### لا توجد بيانات لنطاق 30 يوم

**المشكلة:** استخراج 30 يوم يعود فارغاً لكن 7 أيام يعمل

**الأسباب المحتملة:**
1. أذونات الرمز — تأكد من أذونات `ads_read` و `read_insights`
2. نطاق التاريخ لا يحتوي بيانات — حساب جديد قد لا يملك 30 يوم من السجل
3. مقاييس كثيرة جداً — جرب مقاييس "التسليم" فقط
4. عدم توافق التقسيمات

#### انتهاء صلاحية الرمز

**الحل:** اذهب إلى مستكشف Graph API، أنشئ رمزاً جديداً، حدّث ملف .env أو رمز الملف الشخصي

#### تحديد المعدل

النظام يتعامل تلقائياً مع:
1. مراقبة رأس `x-ad-account-usage`
2. التباطؤ عند تجاوز الاستخدام 75%
3. تراجع أسي (3 ثانية، 6 ثانية، 12 ثانية، إلخ)

---

## 22. Best Practices / أفضل الممارسات

### English

#### Data Extraction

1. **Start with shorter ranges** — Test with last_7d before pulling last_90d
2. **Use fewer breakdowns** — Each breakdown multiplies data volume
3. **Select specific metrics** — "Custom Selection" > "All" when you know what you need
4. **Use time_increment wisely** — `1` (daily) for trends, `all_days` for totals
5. **Schedule extractions** during low-traffic hours to avoid rate limits

#### Campaign Management

1. **Always create campaigns as PAUSED** — Review before activating
2. **Set budgets > $1** — The system enforces minimum $1 daily budget
3. **Use the Duplicate feature** — Faster than creating from scratch
4. **Monitor bleeder alerts daily** — Stop wasting money on underperformers

#### A/B Testing

1. **Run tests for at least 7 days** — Avoid making decisions too early
2. **Use the sample size calculator** — Know how much data you need before starting
3. **Test one variable at a time** — Isolate what's causing the difference
4. **Wait for 95% confidence** before declaring a winner

#### Budget Optimization

1. **Check spend pacing weekly** — Ensure you're on track for monthly goals
2. **Use Custom Weights allocation** — Give more budget to proven winners
3. **Set stop-loss rules** — Automatically pause ads that exceed your max CPA
4. **Review frequency** — Pause ads when frequency > 3.5 to avoid fatigue

#### Profiles

1. **Create separate profiles per brand** — Keep credentials and benchmarks isolated
2. **Set industry-specific benchmarks** — E-commerce CTR benchmarks differ from SaaS
3. **Export profiles regularly** — Backup your configuration
4. **Use tags for organization** — e.g., "Q1-2025", "holiday-campaign", "retargeting"

### العربية

#### استخراج البيانات

1. **ابدأ بنطاقات أقصر** — اختبر بـ last_7d قبل سحب last_90d
2. **استخدم تقسيمات أقل** — كل تقسيم يضاعف حجم البيانات
3. **اختر مقاييس محددة** — "الاختيار المخصص" أفضل من "الكل"
4. **استخدم فترة الزيادة بحكمة** — `1` (يومي) للاتجاهات، `all_days` للمجاميع
5. **جدولة الاستخراج** خلال ساعات الذروة المنخفضة

#### إدارة الحملات

1. **أنشئ الحملات دائماً بحالة متوقف مؤقتاً** — راجع قبل التفعيل
2. **اضبط ميزانيات > $1** — النظام يفرض حد أدنى $1 يومياً
3. **استخدم ميزة النسخ** — أسرع من الإنشاء من الصفر
4. **راقب تنبيهات الهدر يومياً** — أوقف هدر المال على الإعلانات الضعيفة

#### اختبارات A/B

1. **شغّل الاختبارات لمدة 7 أيام على الأقل**
2. **استخدم حاسبة حجم العينة**
3. **اختبر متغيراً واحداً في كل مرة**
4. **انتظر ثقة 95%** قبل إعلان الفائز

---

## 23. API Reference / مرجع API

### English

#### Base URL
```
https://graph.facebook.com/v25.0
```

#### Authentication
All requests require `access_token` parameter.

#### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/me` | GET | Validate token, get user info |
| `/{account_id}` | GET | Account information |
| `/{account_id}/campaigns` | GET | List campaigns |
| `/{account_id}/campaigns` | POST | Create campaign |
| `/{campaign_id}` | POST | Update campaign |
| `/{campaign_id}` | DELETE | Delete campaign |
| `/{account_id}/adsets` | GET | List ad sets |
| `/{account_id}/adsets` | POST | Create ad set |
| `/{account_id}/ads` | GET | List ads |
| `/{account_id}/ads` | POST | Create ad |
| `/{account_id}/insights` | GET | Get insights (sync) |
| `/{account_id}/insights` | POST | Create async report |
| `/{account_id}/customaudiences` | GET | List custom audiences |
| `/{account_id}/customaudiences` | POST | Create custom audience |
| `/{account_id}/adcreatives` | GET | List ad creatives |
| `/{account_id}/targetingbrowse` | GET | Browse targeting options |
| `/{account_id}/targetingsearch` | GET | Search targeting options |
| `/{account_id}/reachestimate` | GET | Estimate audience reach |

#### Rate Limits

- **Account-level**: 180 calls per hour per ad account
- **App-level**: Varies by app tier
- Monitor via `x-ad-account-usage` response header
- Exponential backoff on codes: 17, 32, 613, 80000, 80003

#### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1 | Unknown error / Request too large | Reduce data scope or use async |
| 17 | Too many API calls | Wait and retry with backoff |
| 32 | Rate limit reached | Wait and retry with backoff |
| 100 | Invalid parameter | Check parameter format |
| 102 | Session expired | Refresh access token |
| 104 | Invalid token | Generate new token |
| 190 | Token expired/invalid | Generate new token |
| 200 | Insufficient permissions | Request additional permissions |
| 613 | Calls limit reached | Wait and retry with backoff |
| 80000 | Too many queries | Reduce query complexity |
| 80003 | Too many queries | Reduce query complexity |

### العربية

#### عنوان URL الأساسي
```
https://graph.facebook.com/v25.0
```

#### حدود المعدل

- **مستوى الحساب**: 180 طلب في الساعة لكل حساب إعلانات
- **مستوى التطبيق**: يختلف حسب مستوى التطبيق
- المراقبة عبر رأس استجابة `x-ad-account-usage`
- تراجع أسي عند الأخطاء: 17، 32، 613، 80000، 80003

---

## 24. Glossary / المصطلحات

| English | Arabic | Definition |
|---------|--------|------------|
| **Campaign** | حملة | Top-level ad structure containing ad sets |
| **Ad Set** | مجموعة إعلانات | Contains targeting, budget, schedule settings |
| **Ad** | إعلان | The actual creative shown to users |
| **Creative** | إبداع | The image/video/text of an ad |
| **Impression** | مرة ظهور | One display of your ad |
| **Click** | نقرة | User clicks on your ad |
| **Conversion** | تحويل | User completes desired action |
| **CTR** | نسبة النقر إلى الظهور | Click-Through Rate |
| **CPC** | تكلفة النقرة | Cost Per Click |
| **CPM** | تكلفة لكل ألف ظهور | Cost Per 1000 Impressions |
| **CPA** | تكلفة لكل إجراء | Cost Per Action/Conversion |
| **ROAS** | العائد على الإنفاق الإعلاني | Return On Ad Spend |
| **CVR** | معدل التحويل | Conversion Rate |
| **AOV** | متوسط قيمة الطلب | Average Order Value |
| **Frequency** | التكرار | Average times ad shown per person |
| **Reach** | الوصول | Number of unique people who saw ad |
| **Spend** | الإنفاق | Total money spent |
| **Budget** | الميزانية | Amount allocated for spending |
| **Targeting** | الاستهداف | Criteria for who sees the ad |
| **Audience** | الجمهور | Group of people targeted |
| **Lookalike** | جمهور مشابه | Similar audience based on seed |
| **Pixel** | البكسل | Tracking code on your website |
| **Attribution** | الإسناد | Credit assignment for conversions |
| **Breakdown** | التقسيم | Splitting data by dimension |
| **Preset** | إعداد مسبق | Pre-configured date range |
| **Bleeder** | مُهدر | Ad wasting money with poor performance |
| **Fatigue** | إرهاق | Declining performance from overexposure |
| **DAX** | DAX | Data Analysis Expressions (Power BI) |
| **KPI** | مؤشر أداء رئيسي | Key Performance Indicator |

---

*This book was generated for Meta Ads Ultimate Dashboard v4. For updates and support, visit the [GitHub repository](https://github.com/amrelnagar286/meta-ads-kit).*

*تم إنشاء هذا الكتاب للوحة تحكم إعلانات ميتا الشاملة الإصدار الرابع.*
