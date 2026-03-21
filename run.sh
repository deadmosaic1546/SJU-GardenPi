env $(grep -v '^#' garden-web.env | xargs) \
    .venv/bin/python -m flaskr