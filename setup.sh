mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = true\n\
corsAllowedOrigins = *\n\
enableWebsocketCompression = false\n\
enableXsrfProtection = false\n\
\n\
" > ~/.streamlit/config.toml
