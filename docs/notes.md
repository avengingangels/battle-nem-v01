Note that I changed the shortcut for "Run Selection/Line in python terminal" and removed the when condition which was:

editorTextFocus && !findInputFocussed && !jupyter.ownsSelection && !notebookEditorFocused && !replaceInputFocussed && editorLangId == 'python' && activeEditor != 'workbench.editor.interactive'