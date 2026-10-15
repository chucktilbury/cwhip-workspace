message(FATAL_ERROR
    "${APP} unavailable: enable CWHIP_BUILD_CEDIT/CWHIP_BUILD_CDBG as appropriate, "
    "CWHIP_GTK=ON and CWHIP_GTK_SOURCEVIEW=ON, with GTK 4 >= 4.10 and "
    "GtkSourceView 5 development files. Compiler-only builds can use target cwhip.")
