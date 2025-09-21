from ainfo import parse_data
from ainfo.extractors.jobs import extract_job_postings


def test_extract_job_postings_from_structured_sections() -> None:
    html = (
        "<html><body>"
        '<section class="job">'
        "<h2>Senior Developer</h2>"
        "<p>Company: Acme Corp</p>"
        "<p>Location: Remote</p>"
        "<p>Employment Type: Full-time</p>"
        "<p>Salary: $100k</p>"
        '<a href="https://example.com/apply" class="apply">Apply now</a>'
        "</section>"
        '<div class="job">'
        "<h3>Junior Developer</h3>"
        "<ul>"
        "<li>Location: Berlin, Germany</li>"
        "<li>Type: Part-time</li>"
        "<li>Experience: 1-2 years</li>"
        "</ul>"
        "</div>"
        "</body></html>"
    )

    doc = parse_data(html, url="https://example.com")
    postings = extract_job_postings(doc)

    assert postings == [
        {
            "company": "Acme Corp",
            "location": "Remote",
            "employment_type": "Full-time",
            "salary": "$100k",
            "position": "Senior Developer",
            "apply_url": "https://example.com/apply",
        },
        {
            "location": "Berlin, Germany",
            "employment_type": "Part-time",
            "experience": "1-2 years",
            "position": "Junior Developer",
        },
    ]


def test_extract_job_posting_without_explicit_classnames() -> None:
    html = (
        "<html><body>"
        "<article>"
        "<p>Position: Data Analyst</p>"
        "<p>Location: London, UK</p>"
        "<p>Employment Type: Contract</p>"
        "</article>"
        "<div><p>Location: Just a place</p></div>"
        "</body></html>"
    )

    doc = parse_data(html, url="https://example.com/jobs")
    postings = extract_job_postings(doc)

    assert postings == [
        {
            "position": "Data Analyst",
            "location": "London, UK",
            "employment_type": "Contract",
        }
    ]


def test_extract_job_postings_with_german_keywords() -> None:
    html = (
        "<html><body>"
        '<section class="stellenangebot">'
        "<h2>Data Scientist (m/w/d)</h2>"
        "<p>Unternehmen: Beispiel GmbH</p>"
        "<p>Standort: München</p>"
        "<p>Anstellungsart: Vollzeit</p>"
        "<p>Gehalt: 60.000€</p>"
        '<a href="https://example.com/bewerben" title="Jetzt bewerben">Jetzt bewerben</a>'
        "</section>"
        '<div class="stelle">'
        "<h3>Werkstudent Marketing</h3>"
        "<p>Beschäftigungsart: Teilzeit</p>"
        "<p>Ort: Hamburg</p>"
        "<p>Berufserfahrung: Erste Erfahrungen</p>"
        "</div>"
        "</body></html>"
    )

    doc = parse_data(html, url="https://example.de/jobs")
    postings = extract_job_postings(doc)

    assert postings == [
        {
            "company": "Beispiel GmbH",
            "location": "München",
            "employment_type": "Vollzeit",
            "salary": "60.000€",
            "position": "Data Scientist (m/w/d)",
            "apply_url": "https://example.com/bewerben",
        },
        {
            "employment_type": "Teilzeit",
            "location": "Hamburg",
            "experience": "Erste Erfahrungen",
            "position": "Werkstudent Marketing",
        },
    ]
