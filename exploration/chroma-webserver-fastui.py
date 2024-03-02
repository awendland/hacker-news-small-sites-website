from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui import prebuilt_html
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import fastui_form
from pydantic import BaseModel, Field

app = FastAPI()


class Entries(BaseModel):
    title: str
    num_score: int
    num_comments: int
    pub_date: date


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def search_page(query: str | None = None) -> list[AnyComponent]:
    """
    Show a search function, `/api` is the endpoint the frontend will connect to
    when a user visits `/` to fetch components to render.
    """
    if query:
        results = [
            {
                "title": "title",
                "num_score": 1,
                "num_comments": 2,
                "pub_date": date(2021, 1, 1),
            },
            {
                "title": "title2",
                "num_score": 3,
                "num_comments": 4,
                "pub_date": date(2021, 1, 2),
            },
        ]
    else:
        results = []
    return [
        c.Page(  # Page provides a basic container for components
            components=[
                c.Heading(text="Hacker News Small Sites", level=2),
                c.Div(
                    components=[
                        c.Form(
                            submit_url="/api/search",
                            form_fields=[
                                c.FormFieldInput(name="query", title="Search")
                            ],
                        ),
                    ]
                ),
                c.Div(
                    components=[
                        c.Div(
                            components=[
                                c.Table(
                                    data=results,
                                    data_model=Entries,
                                    columns=[
                                        DisplayLookup(field="title"),
                                        DisplayLookup(field="num_score"),
                                        DisplayLookup(field="num_comments"),
                                        DisplayLookup(field="pub_date"),
                                    ],
                                )
                            ]
                        ),
                        c.Div(
                            components=[
                                c.ServerLoad(
                                    path="/readable-entry",
                                    load_trigger=PageEvent(name="readable-entry"),
                                    components=[c.Text(text="before")],
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]


class SearchForm(BaseModel):
    query: str = Field(title="Search")


@app.post("/api/search", response_model=FastUI, response_model_exclude_none=True)
async def login_form_post(form: Annotated[SearchForm, fastui_form(SearchForm)]):
    return [c.FireEvent(event=GoToEvent(url="/", query={"query": form.query}))]


@app.get("/api/readable-entry", response_model=FastUI, response_model_exclude_none=True)
def search_results(user_id: int) -> list[AnyComponent]:
    """
    User profile page, the frontend will fetch this when the user visits `/user/{id}/`.
    """
    try:
        user = next(u for u in [] if u.id == user_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        c.Page(
            components=[
                c.Heading(text=user.name, level=2),
                c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
                c.Details(data=user),
            ]
        ),
    ]


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""  # noqa: E501
    return HTMLResponse(prebuilt_html(title="Hacker News Small Sites"))
