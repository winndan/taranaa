from fasthtml.common import *
from monsterui.all import *
from fasthtml.svg import *


# Using the "slate" theme with Highlight.js enabled
hdrs = Theme.slate.headers(highlightjs=True)
app, rt = fast_app(hdrs=hdrs, live=True)

@rt
def index():    
    background_style = {
    'background-image': 'url("/assets/auth.jpg")',
    'background-size': 'cover',
    'background-position': 'center',
    'background-repeat': 'no-repeat'
}   
    
    left = Div(
    cls="col-span-1 hidden flex-col justify-between p-8 text-white lg:flex",
    style=background_style
)(
    Div(cls=(TextT.bold))("Tarana"),
    Blockquote(cls="space-y-2")(
        P(cls=TextT.lg)("\"This library has saved me countless hours of work and helped me deliver stunning designs to my clients faster than ever before.\""),
        Footer(cls=TextT.sm)("Sofia Davis")
    )
)



    right = Div(cls="col-span-2 flex flex-col p-8 lg:col-span-1")(
        DivRAligned(Button("back home", cls=ButtonT.ghost)),
        DivCentered(cls='flex-1')(
            Container(
                DivVStacked(
                    H3("Sign in with Socials"),
                    Small("Click below to sign in using your Google account", cls=TextT.muted)),
                Form(
                    Button(Span("G",
        cls=(
            "mr-2 font-bold text-2xl "  # Bigger text size
            "bg-clip-text text-transparent "  # Makes gradient apply to text
            "bg-[conic-gradient(at_center,_#4285F4_0deg_90deg,_#EA4335_90deg_180deg,_#FBBC05_180deg_270deg,_#34A853_270deg)]"
        ),
    ),
    "Sign in with Google",
    cls=(ButtonT.primary, "w-full")),
                    cls='space-y-6'),
                cls="space-y-6")))

    return Title("Auth Example"), Grid(left, right, cols=2, gap=0, cls='h-screen')

serve()
