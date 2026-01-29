diff --git a/openai_stages/run_all_stages.py b/openai_stages/run_all_stages.py
index bdbad19..c6391c7 100644
--- a/openai_stages/run_all_stages.py
+++ b/openai_stages/run_all_stages.py
@@ -13,6 +13,7 @@ Usage:
   python run_all_stages.py --test      # 3 test regions
   python run_all_stages.py --priority  # 15 priority regions
   python run_all_stages.py --all       # All 38 German NUTS-2 regions
+  python run_all_stages.py --custom DE11,DE21,DE94  # Custom NUTS-2 codes
   python run_all_stages.py --from 3    # Resume from Stage 3
 """
 
@@ -73,7 +74,7 @@ def run_pipeline(regions: dict, start_from: int = 1):
         print("▶" * 35)
         
         start = datetime.now()
-        run_stage2()
+        run_stage2(regions_filter=set(regions.keys()))
         stage_times["Stage 2"] = datetime.now() - start
         print(f"\n⏱ Stage 2 completed in {stage_times['Stage 2']}")
     else:
@@ -88,7 +89,7 @@ def run_pipeline(regions: dict, start_from: int = 1):
         print("▶" * 35)
         
         start = datetime.now()
-        run_stage3()
+        run_stage3(regions_filter=set(regions.keys()))
         stage_times["Stage 3"] = datetime.now() - start
         print(f"\n⏱ Stage 3 completed in {stage_times['Stage 3']}")
     else:
@@ -103,7 +104,7 @@ def run_pipeline(regions: dict, start_from: int = 1):
         print("▶" * 35)
         
         start = datetime.now()
-        run_stage4()
+        run_stage4(regions_filter=set(regions.keys()))
         stage_times["Stage 4"] = datetime.now() - start
         print(f"\n⏱ Stage 4 completed in {stage_times['Stage 4']}")
     else:
@@ -178,28 +179,57 @@ Examples:
   python run_all_stages.py --test           # Quick test with 3 regions
   python run_all_stages.py --priority       # 15 automotive-heavy regions
   python run_all_stages.py --all            # All 38 German NUTS-2 regions
+  python run_all_stages.py --custom DE11,DE21,DE94  # Custom NUTS-2 codes
   python run_all_stages.py --from 3         # Resume from Stage 3
   python run_all_stages.py --from 5         # Just run validation & RAVI
         """
     )
-    
+
     group = parser.add_mutually_exclusive_group()
-    group.add_argument('--test', action='store_true',
-                      help='Test with 3 regions (Stuttgart, Oberbayern, Braunschweig)')
-    group.add_argument('--priority', action='store_true',
-                      help='Priority automotive regions (15 regions)')
-    group.add_argument('--all', action='store_true',
-                      help='All 38 German NUTS-2 regions')
-    group.add_argument('--remaining', action='store_true',
-                      help='Remaining unprocessed regions (23 regions)')
+    group.add_argument(
+        '--test',
+        action='store_true',
+        help='Test with 3 regions (Stuttgart, Oberbayern, Braunschweig)',
+    )
+    group.add_argument(
+        '--priority',
+        action='store_true',
+        help='Priority automotive regions (15 regions)',
+    )
+    group.add_argument(
+        '--all',
+        action='store_true',
+        help='All 38 German NUTS-2 regions',
+    )
+    group.add_argument(
+        '--remaining',
+        action='store_true',
+        help='Remaining unprocessed regions (23 regions)',
+    )
+    group.add_argument(
+        '--custom',
+        type=str,
+        help='Comma-separated NUTS-2 codes (e.g., DE11,DE21,DE94)',
+    )
 
-    parser.add_argument('--from', dest='start_from', type=int, default=1,
-                       help='Start from stage N (1-6). Use to resume failed runs.')
+    parser.add_argument(
+        '--from',
+        dest='start_from',
+        type=int,
+        default=1,
+        help='Start from stage N (1-6). Use to resume failed runs.',
+    )
 
     args = parser.parse_args()
 
     # Select regions
-    if args.all:
+    if args.custom:
+        custom_codes = [code.strip().upper() for code in args.custom.split(",") if code.strip()]
+        regions = {code: ALL_REGIONS[code] for code in custom_codes if code in ALL_REGIONS}
+        missing = sorted(set(custom_codes) - set(regions.keys()))
+        if missing:
+            print(f"WARNING: Unknown region codes ignored: {', '.join(missing)}")
+    elif args.all:
         regions = ALL_REGIONS
     elif args.remaining:
         regions = REMAINING_REGIONS
@@ -216,4 +246,4 @@ Examples:
     os.makedirs("results", exist_ok=True)
     
     # Run pipeline
-    run_pipeline(regions, start_from=args.start_from)
\ No newline at end of file
+    run_pipeline(regions, start_from=args.start_from)
diff --git a/openai_stages/run_stage1_openai.py b/openai_stages/run_stage1_openai.py
index ac24474..96dfaf4 100644
--- a/openai_stages/run_stage1_openai.py
+++ b/openai_stages/run_stage1_openai.py
@@ -76,7 +76,7 @@ def build_prompt(nuts2_code: str, nuts2_name: str) -> str:
     return f"""You are an expert in the European automotive industry.
 
 TASK:
-For the German NUTS-2 region "{nuts2_code} — {nuts2_name}", identify the most
+For the German NUTS-2 region "{nuts2_code} — {nuts2_name}", identify the 3 most
 significant automotive companies that operate production or manufacturing facilities
 in this region.
 
@@ -118,6 +118,9 @@ Return ONLY valid JSON in the following structure (no markdown, no explanations)
     }}
   ]
 }}
+
+IMPORTANT:
+- Return EXACTLY 3 companies (most significant only).
 """
@@ -149,14 +152,19 @@ def run_stage1(nuts2_code: str, nuts2_name: str) -> dict:
     
     # Parse JSON response
     try:
-        # Try to find JSON object
-        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
+        # Try to find JSON object (strip code fences if present)
+        cleaned = response_text.strip()
+        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
+        cleaned = re.sub(r"```$", "", cleaned).strip()
+
+        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
         if json_match:
             data = json.loads(json_match.group(0))
         else:
-            data = json.loads(response_text)
+            data = json.loads(cleaned)
     except json.JSONDecodeError as e:
         print(f"WARNING: Failed to parse JSON for {nuts2_code} - {e}")
+        print(f"[STAGE1] Full response for {nuts2_code}: {response_text}")
         data = {
             "nuts2_code": nuts2_code,
             "nuts2_name": nuts2_name,
@@ -169,6 +177,8 @@ def run_stage1(nuts2_code: str, nuts2_name: str) -> dict:
     
     if "companies" not in data:
         data["companies"] = []
+
+    data["companies"] = data["companies"][:3]
diff --git a/openai_stages/run_stage2_openai.py b/openai_stages/run_stage2_openai.py
index 22ee82e..39249dd 100644
--- a/openai_stages/run_stage2_openai.py
+++ b/openai_stages/run_stage2_openai.py
@@ -131,7 +131,7 @@ def run_stage2_for_company(company_name: str, nuts2_code: str, nuts2_name: str)
 # BATCH RUNNER
 # ============================================================
 
-def run_stage2():
+def run_stage2(regions_filter: set | None = None):
@@ -161,6 +161,8 @@ def run_stage2():
             stage1_data = json.load(f)
         
         nuts2_code = stage1_data.get("nuts2_code", "")
+        if regions_filter and nuts2_code not in regions_filter:
+            continue
         nuts2_name = stage1_data.get("nuts2_name", "")
         companies = stage1_data.get("companies", [])
diff --git a/openai_stages/run_stage3_openai.py b/openai_stages/run_stage3_openai.py
index 15533a1..c27cb74 100644
--- a/openai_stages/run_stage3_openai.py
+++ b/openai_stages/run_stage3_openai.py
@@ -186,7 +186,7 @@ def run_stage3_for_plant(company: str, plant_name: str, city: str, nuts2_code: s
 # BATCH RUNNER
 # ============================================================
 
-def run_stage3():
+def run_stage3(regions_filter: set | None = None):
@@ -217,6 +217,8 @@ def run_stage3():
         
         company = stage2_data.get("company", "Unknown")
         nuts2_code = stage2_data.get("nuts2_code", "")
+        if regions_filter and nuts2_code not in regions_filter:
+            continue
         nuts2_name = stage2_data.get("nuts2_name", "")
         plants = stage2_data.get("plants", [])
diff --git a/openai_stages/run_stage4_openai.py b/openai_stages/run_stage4_openai.py
index 25f150e..a1a5705 100644
--- a/openai_stages/run_stage4_openai.py
+++ b/openai_stages/run_stage4_openai.py
@@ -175,7 +175,7 @@ def run_stage4_for_plant(company: str, plant: str, city: str, nuts2_code: str) -
 # BATCH RUNNER
 # ============================================================
 
-def run_stage4():
+def run_stage4(regions_filter: set | None = None):
@@ -216,6 +216,8 @@ def run_stage4():
         plant = stage3_data.get("plant", "Unknown")
         city = stage3_data.get("city", "")
         nuts2_code = stage3_data.get("nuts2_code", "")
+        if regions_filter and nuts2_code not in regions_filter:
+            continue
