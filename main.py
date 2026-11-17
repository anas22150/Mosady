import flet as ft
import httpx

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"


def main(page: ft.Page):
    page.title = "خبير AI"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F3F6FC"
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    api_key = ft.TextField(
        label="مفتاح Claude API",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        hint_text="أدخل مفتاح API الخاص بك",
    )
    ask_box = ft.TextField(label="اكتب سؤالك", multiline=True, min_lines=3, max_lines=6,
                           border_radius=12)
    lesson_box = ft.TextField(label="الصق نص الدرس هنا", multiline=True, min_lines=5,
                              max_lines=12, border_radius=12)
    number = ft.Dropdown(label="عدد الأسئلة", value="10",
                         options=[ft.dropdown.Option(str(x)) for x in (5, 10, 15, 20, 25)])
    kind = ft.Dropdown(label="نوع الأسئلة", value="متنوع",
                       options=[ft.dropdown.Option(x) for x in
                                ("متنوع", "اختيار من متعدد", "صح أو خطأ", "أكمل", "مقالي")])
    output = ft.Text("ستظهر الإجابة هنا.", selectable=True, color="#1E293B")
    status = ft.Text("", color="#64748B")

    def notify(msg):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    async def ask_claude(prompt, system, max_tokens):
        key = (api_key.value or "").strip()
        if not key:
            notify("أدخل مفتاح Claude API أولًا.")
            return None
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
            if response.is_error:
                try:
                    detail = response.json().get("error", {}).get("message", response.text)
                except Exception:
                    detail = response.text
                notify(f"خطأ من Claude ({response.status_code}): {detail}")
                return None
            data = response.json()
            return "\n".join(
                block.get("text", "") for block in data.get("content", [])
                if block.get("type") == "text"
            ) or "لم يرجع Claude نصًا في الرد."
        except httpx.TimeoutException:
            notify("انتهت مهلة الاتصال. حاول مرة أخرى.")
        except Exception as ex:
            notify("تعذر الاتصال بخدمة Claude: " + str(ex))
        return None

    async def ask_click(e):
        if not (ask_box.value or "").strip():
            notify("اكتب سؤالك أولًا.")
            return
        status.value, output.value = "جاري تجهيز الإجابة...", ""
        page.update()
        answer = await ask_claude(
            ask_box.value.strip(),
            "أنت مساعد تعليمي عربي. أجب بدقة وبأسلوب واضح ومناسب للطلاب.",
            1800,
        )
        if answer:
            output.value = answer
        status.value = ""
        page.update()

    async def exam_click(e):
        lesson = (lesson_box.value or "").strip()
        if not lesson:
            notify("أضف نص الدرس أولًا.")
            return
        status.value, output.value = "جاري إنشاء الامتحان...", ""
        page.update()
        prompt = (
            f"أنشئ امتحانًا من الدرس التالي. العدد: {int(number.value or '10')}. "
            f"النوع: {kind.value or 'متنوع'}. رقّم الأسئلة ثم ضع نموذج الإجابة في قسم منفصل. "
            "لا تضف معلومات من خارج الدرس.\n\n" + lesson
        )
        exam = await ask_claude(
            prompt,
            "أنت متخصص في إعداد الاختبارات باللغة العربية. التزم بمحتوى الدرس.",
            3500,
        )
        if exam:
            output.value = exam
        status.value = ""
        page.update()

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("خبير AI", size=28, weight=ft.FontWeight.BOLD, color="#172554"),
                ft.Text("مساعدك الذكي للفهم والمذاكرة", color="#64748B")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor="white", padding=18, border_radius=20
        ),
        ft.Container(content=ft.Column([
            ft.Text("إعداد Claude", size=18, weight=ft.FontWeight.BOLD),
            api_key,
            ft.Text("الاتصال مباشر بخدمة Claude من التطبيق، ولا يحتاج إلى خادم منفصل. "
                    "أدخل مفتاحك عند فتح التطبيق. لا تشارك المفتاح مع أحد.",
                    size=12, color="#64748B")
        ], spacing=10), bgcolor="white", padding=16, border_radius=18),
        ft.Container(content=ft.Column([
            ft.Text("اسأل خبير AI", size=19, weight=ft.FontWeight.BOLD, color="#1D4ED8"),
            ask_box,
            ft.Button("إرسال السؤال", icon=ft.Icons.AUTO_AWESOME,
                      on_click=ask_click,
                      style=ft.ButtonStyle(bgcolor="#2563EB", color="white"))
        ], spacing=12), bgcolor="white", padding=16, border_radius=18),
        ft.Container(content=ft.Column([
            ft.Text("إنشاء امتحان من الدرس", size=19, weight=ft.FontWeight.BOLD,
                    color="#6D28D9"),
            lesson_box, number, kind,
            ft.Button("إنشاء الامتحان", icon=ft.Icons.QUIZ,
                      on_click=exam_click,
                      style=ft.ButtonStyle(bgcolor="#6D28D9", color="white"))
        ], spacing=12), bgcolor="white", padding=16, border_radius=18),
        ft.Container(content=ft.Column([
            ft.Text("النتيجة", size=18, weight=ft.FontWeight.BOLD),
            status, output
        ], spacing=10), bgcolor="white", padding=16, border_radius=18),
        ft.Text("يتطلب اتصالًا بالإنترنت ومفتاح Claude API صالحًا. قد تُحتسب تكلفة على استخدام API.",
                size=11, color="#94A3B8", text_align=ft.TextAlign.CENTER)
    )


ft.run(main)
