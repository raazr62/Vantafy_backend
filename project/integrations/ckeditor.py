WORD_FONT_SIZES = [
    9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 26, 28, 32, 36, 48, 72
]

CKEDITOR_5_CONFIGS = {
    # 1. Default Configuration (Standard Rich Text)
    "default": {
        "toolbar": [
            "heading",
            "|",
            "fontSize",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "|",
            "undo",
            "redo",
        ],
        "fontSize": {
            "options": WORD_FONT_SIZES,
            "supportAllValues": True,
        },
    },

    # 2. Minimal Configuration (Lightweight Inline Editor)
    "minimal": {
        "toolbar": [
            "bold",
            "italic",
            "underline",
            "fontSize",
            "link",
            "bulletedList",
            "|",
            "undo",
            "redo",
        ],
        "fontSize": {
            "options": WORD_FONT_SIZES,
            "supportAllValues": True,
        },
    },

    # 3. Extends Configuration (Medium-Weight Rich Content)
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "numberedList",
            "bulletedList",
            "|",
            "link",
            "blockQuote",
            "insertTable",
        ],
        "toolbar": [
            "heading",
            "|",
            "fontSize",
            "fontColor",
            "fontBackgroundColor",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "subscript",
            "superscript",
            "highlight",
            "|",
            "alignment",
            "outdent",
            "indent",
            "|",
            "link",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "insertTable",
            "mediaEmbed",
            "removeFormat",
            "|",
            "undo",
            "redo",
        ],
        "fontSize": {
            "options": WORD_FONT_SIZES,
            "supportAllValues": True,
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ]
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Heading 4", "class": "ck-heading_heading4"},
            ]
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True,
            }
        },
    },

    # 4. Full / Advanced Admin Configuration
    "full": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "heading4",
            "|",
            "numberedList",
            "bulletedList",
            "|",
            "link",
            "blockQuote",
            "insertTable",
            "mediaEmbed",
            "codeBlock",
        ],
        "toolbar": [
            "heading",
            "|",
            "fontSize",
            "fontColor",
            "fontBackgroundColor",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "code",
            "subscript",
            "superscript",
            "highlight",
            "|",
            "alignment",
            "outdent",
            "indent",
            "|",
            "link",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "insertTable",
            "mediaEmbed",
            "codeBlock",
            "horizontalLine",
            "|",
            "removeFormat",
            "sourceEditing",
            "|",
            "undo",
            "redo",
        ],
        "fontSize": {
            "options": WORD_FONT_SIZES,
            "supportAllValues": True,
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ]
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1 (Main)", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2 (Section)", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3 (Sub-section)", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Heading 4 (Minor)", "class": "ck-heading_heading4"},
                {"model": "heading5", "view": "h5", "title": "Heading 5", "class": "ck-heading_heading5"},
                {"model": "heading6", "view": "h6", "title": "Heading 6", "class": "ck-heading_heading6"},
            ]
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True,
            }
        },
    },

    # 5. CMS & Legal Page Configuration
    "cms": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "numberedList",
            "bulletedList",
            "|",
            "link",
            "blockQuote",
            "insertTable",
        ],
        "toolbar": [
            "heading",
            "|",
            "fontSize",
            "fontColor",
            "fontBackgroundColor",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "highlight",
            "|",
            "alignment",
            "outdent",
            "indent",
            "|",
            "link",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "insertTable",
            "removeFormat",
            "sourceEditing",
            "|",
            "undo",
            "redo",
        ],
        "fontSize": {
            "options": WORD_FONT_SIZES,
            "supportAllValues": True,
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ]
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Title (H1)", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Section Title (H2)", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Sub-section (H3)", "class": "ck-heading_heading3"},
            ]
        },
    },
}