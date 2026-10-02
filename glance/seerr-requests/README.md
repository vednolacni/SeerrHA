# Seerr Requests

The requests waiting in Seerr (or Overseerr, or Jellyseerr): poster, title,
who asked and when, and for TV the seasons they picked. Each one links to its
page in Seerr, where approving is a click away.

If you run Home Assistant, the widget can also carry Approve and Decline
buttons of its own. They are off by default; [see below](#approve-and-decline-buttons).

![Pending requests](preview.png)

## Environment variables

- `SEERR_URL`: the address Glance uses to reach Seerr, e.g.
  `http://192.168.1.10:5055` or `http://seerr:5055` inside Docker.
- `SEERR_API_KEY`: Seerr → Settings → General → API Key.

The widget only reads from Seerr, so Seerr's CSRF Protection setting does not
affect it.

## Options

| Option | Default | What it does |
|---|---|---|
| `seerr-url` | | Where Glance fetches from. Set from `SEERR_URL`. |
| `api-key` | | Set from `SEERR_API_KEY`. |
| `link-url` | `seerr-url` | Where your browser reaches Seerr, if that differs from `seerr-url` (a Docker hostname, say). Used for the title and poster links. |
| `filter` | `pending` | `pending`, `all`, `approved`, `processing`, `available`, `unavailable` or `failed`. |
| `sort` | `added` | `added` or `modified`. |
| `max-requests` | `10` | How many requests to show. Each one costs one extra API call per refresh, for its title and poster. |
| `collapse-after` | `4` | Rows shown before "Show more". |
| `show-posters` | `true` | Set to `false` for a text-only list. |
| `ha-webhook-url` | `""` | Turns on the Approve and Decline buttons. See below. |

`title-url` opens the pending tab of Seerr's request list at `SEERR_URL`. It is
plain Glance config, not part of the template, so if you set `link-url` or
change `filter`, edit it to match.

## Widget YAML

Paste this under a column's `widgets:`, or save it as `seerr-requests.yml` and
use `- $include: seerr-requests.yml`.

```yaml
- type: custom-api
  title: Seerr Requests
  title-url: ${SEERR_URL}/requests?filter=pending
  cache: 5m
  options:
    seerr-url: ${SEERR_URL}
    api-key: ${SEERR_API_KEY}
    # link-url: https://seerr.example.com   # where browsers reach Seerr, if not seerr-url
    filter: pending       # pending | all | approved | processing | available | unavailable | failed
    sort: added           # added | modified
    max-requests: 10
    collapse-after: 4
    show-posters: true
    ha-webhook-url: ""    # set to enable Approve / Decline, see README
  template: |
    {{ $baseUrl := .Options.StringOr "seerr-url" "" | trimSuffix "/" }}
    {{ $apiKey := .Options.StringOr "api-key" "" }}
    {{ $linkUrl := .Options.StringOr "link-url" $baseUrl | trimSuffix "/" }}
    {{ $filter := .Options.StringOr "filter" "pending" }}
    {{ $sort := .Options.StringOr "sort" "added" }}
    {{ $max := .Options.IntOr "max-requests" 10 }}
    {{ $collapseAfter := .Options.IntOr "collapse-after" 4 }}
    {{ $showPosters := .Options.BoolOr "show-posters" true }}
    {{ $webhook := .Options.StringOr "ha-webhook-url" "" }}

    {{ $list := newRequest (concat $baseUrl "/api/v1/request")
      | withParameter "take" (printf "%d" $max)
      | withParameter "filter" $filter
      | withParameter "sort" $sort
      | withHeader "Accept" "application/json"
      | withHeader "X-Api-Key" $apiKey
      | getResponse }}

    {{ if ne $list.Response.StatusCode 200 }}
      <div class="text-center">
        <p class="color-negative">Could not load requests (HTTP {{ $list.Response.StatusCode }})</p>
        <p class="size-h6 color-subdue margin-top-3">
          {{ if eq $list.Response.StatusCode 403 }}Check SEERR_API_KEY.{{ else }}Check SEERR_URL and that Seerr is reachable from Glance.{{ end }}
        </p>
      </div>
    {{ else }}
      {{ $requests := $list.JSON.Array "results" }}
      {{ if eq (len $requests) 0 }}
        <p class="text-center color-subdue">No {{ if ne $filter "all" }}{{ $filter }} {{ end }}requests</p>
      {{ else }}
        {{ if ne $webhook "" }}<iframe name="sink-seerr-requests" title="Fallback target for the Approve and Decline buttons" hidden></iframe>{{ end }}
        <ul class="list list-gap-14 collapsible-container" data-collapse-after="{{ $collapseAfter }}">
        {{ range $requests }}
          {{ $type := .String "type" }}
          {{ $tmdbId := .String "media.tmdbId" }}
          {{ $is4k := .Bool "is4k" }}
          {{ $link := concat $linkUrl "/" $type "/" $tmdbId }}

          {{ $details := newRequest (concat $baseUrl "/api/v1/" $type "/" $tmdbId)
            | withHeader "Accept" "application/json"
            | withHeader "X-Api-Key" $apiKey
            | getResponse }}

          {{ $title := concat "TMDB " $tmdbId }}
          {{ $year := "" }}
          {{ $poster := "" }}
          {{ if eq $details.Response.StatusCode 200 }}
            {{ if eq $type "movie" }}
              {{ $title = $details.JSON.String "title" }}
              {{ $year = findMatch "^[0-9]{4}" ($details.JSON.String "releaseDate") }}
            {{ else }}
              {{ $title = $details.JSON.String "name" }}
              {{ $year = findMatch "^[0-9]{4}" ($details.JSON.String "firstAirDate") }}
            {{ end }}
            {{ $poster = $details.JSON.String "posterPath" }}
          {{ end }}

          {{ $who := .String "requestedBy.displayName" }}
          {{ if eq $who "" }}{{ $who = .String "requestedBy.username" }}{{ end }}
          {{ if eq $who "" }}{{ $who = .String "requestedBy.email" }}{{ end }}

          {{ $requestStatus := .Int "status" }}
          {{ $mediaStatus := .Int "media.status" }}
          {{ if $is4k }}{{ $mediaStatus = .Int "media.status4k" }}{{ end }}
          {{ $statusLabel := "Approved" }}
          {{ $statusClass := "color-primary" }}
          {{ if eq $requestStatus 1 }}{{ $statusLabel = "Pending" }}{{ $statusClass = "color-highlight" }}
          {{ else if eq $requestStatus 3 }}{{ $statusLabel = "Declined" }}{{ $statusClass = "color-negative" }}
          {{ else if eq $requestStatus 4 }}{{ $statusLabel = "Failed" }}{{ $statusClass = "color-negative" }}
          {{ else if eq $mediaStatus 5 }}{{ $statusLabel = "Available" }}{{ $statusClass = "color-positive" }}
          {{ else if eq $mediaStatus 4 }}{{ $statusLabel = "Partial" }}{{ $statusClass = "color-positive" }}
          {{ else if eq $mediaStatus 3 }}{{ $statusLabel = "Processing" }}{{ $statusClass = "color-primary" }}
          {{ end }}

          <li class="flex items-center gap-15">
            {{ if $showPosters }}
              <a href="{{ $link }}" target="_blank" rel="noreferrer" class="shrink-0">
                {{ if ne $poster "" }}
                  <img src="https://image.tmdb.org/t/p/w185{{ $poster }}" alt="" loading="lazy"
                    style="display: block; width: 3.6rem; aspect-ratio: 2 / 3; object-fit: cover; border-radius: var(--border-radius);">
                {{ else }}
                  <div class="color-subdue size-h6 text-center"
                    style="display: flex; align-items: center; justify-content: center; width: 3.6rem; aspect-ratio: 2 / 3; border: 1px dashed currentColor; border-radius: var(--border-radius);">No art</div>
                {{ end }}
              </a>
            {{ end }}
            <div class="flex-1 min-width-0">
              <a href="{{ $link }}" target="_blank" rel="noreferrer"
                class="size-h4 block text-truncate color-primary" title="{{ $title }}">{{ $title }}{{ if ne $year "" }} ({{ $year }}){{ end }}</a>
              <ul class="list-horizontal-text size-h6 margin-top-3">
                <li class="{{ $statusClass }}" data-seerrha-status>{{ $statusLabel }}</li>
                <li>{{ $who }}</li>
                <li {{ .String "createdAt" | parseTime "rfc3339" | toRelativeTime }}></li>
              </ul>
              <ul class="list-horizontal-text size-h6 color-subdue margin-top-3">
                <li>{{ if eq $type "movie" }}Movie{{ else }}Series{{ end }}</li>
                {{ if eq $type "tv" }}
                  {{ $seasons := .Array "seasons" }}
                  {{ if gt (len $seasons) 0 }}
                    <li class="text-truncate">{{ if eq (len $seasons) 1 }}Season{{ else }}Seasons{{ end }} {{ range $i, $s := $seasons }}{{ if $i }}, {{ end }}{{ $s.Int "seasonNumber" }}{{ end }}</li>
                  {{ end }}
                {{ end }}
                {{ if $is4k }}<li>4K</li>{{ end }}
              </ul>
              {{ if and (ne $webhook "") (eq $requestStatus 1) }}
                <form method="post" action="{{ $webhook }}" target="sink-seerr-requests" class="flex gap-10 margin-top-5"
                  onsubmit="var form = this, row = form.closest('li'), status = row.querySelector('[data-seerrha-status]');
                    var body = new URLSearchParams(new FormData(form));
                    body.set('cmd', event.submitter.value);
                    var buttons = form.querySelectorAll('button');
                    row.style.opacity = '0.45';
                    buttons.forEach(function (b) { b.disabled = true; });
                    fetch(form.action, { method: 'POST', mode: 'no-cors', body: body })
                      .then(function () { status.textContent = 'Sent'; })
                      .catch(function () {
                        row.style.opacity = '1';
                        buttons.forEach(function (b) { b.disabled = false; });
                        status.textContent = 'Home Assistant unreachable';
                        status.className = 'color-negative';
                      });
                    return false;">
                  <input type="hidden" name="request_id" value="{{ .Int "id" }}">
                  <button type="submit" name="cmd" value="approve" class="size-h6 color-positive"
                    style="background: none; border: 1px solid currentColor; border-radius: var(--border-radius); padding: 0.2rem 0.8rem; cursor: pointer; font-family: inherit;">Approve</button>
                  <button type="submit" name="cmd" value="decline" class="size-h6 color-negative"
                    style="background: none; border: 1px solid currentColor; border-radius: var(--border-radius); padding: 0.2rem 0.8rem; cursor: pointer; font-family: inherit;">Decline</button>
                </form>
              {{ end }}
            </div>
          </li>
        {{ end }}
        </ul>
      {{ end }}
    {{ end }}
```

## Gallery

`filter: all`, showing the status of each request:

![All requests](preview-all.png)

With the buttons on, after pressing Approve on the first request:

![Approve and Decline buttons](preview-buttons.png)

## Approve and Decline buttons

Glance cannot approve on its own. Its templates run on the Glance server every
time the widget refreshes, so a write call inside one would fire on every
refresh. And calling Seerr from the browser would mean putting the API key in
the page, for anyone who opens it.

So the buttons post to a Home Assistant webhook, and Home Assistant makes the
call with the key it already holds:

```
button in Glance ──POST──▶ Home Assistant webhook ──▶ rest_command ──▶ Seerr
```

The Home Assistant side comes from
[SeerrHA](https://github.com/vednolacni/SeerrHA), which also turns new
requests into phone notifications with the same two buttons.

1. Add `rest_command.seerrha_request_action` to Home Assistant: copy
   [`rest_commands.yaml`](https://github.com/vednolacni/SeerrHA/blob/main/examples/rest_commands.yaml)
   unchanged and include it with `rest_command: !include rest_commands.yaml`.
   Restart once.
2. Import the Glance buttons blueprint and choose a long random webhook id:

   [![Import the blueprint into Home Assistant](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fvednolacni%2FSeerrHA%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fseerrha%2Fseerr_glance_webhook.yaml)

3. In the widget, set the webhook URL and refresh more often, so a decided
   request drops off sooner:

   ```yaml
   cache: 1m
   options:
     ha-webhook-url: http://homeassistant.local:8123/api/webhook/<your id>
   ```

Pressing a button fades the row, and its status reads "Sent" once Home
Assistant has the request. If Home Assistant cannot be reached, the row comes
back and says so. Seerr's answer goes to Home Assistant rather than to the
browser, so a decision Seerr rejects is reported there, as a Home Assistant
notification, and on your phone if you pick one in the blueprint. Picking the
phone also clears the request's notification from it when you decide on the
dashboard.

Worth knowing before you turn this on:

- The webhook id works as a password, and it sits in the page source. Anyone
  who can open your Glance page can approve and decline. Put authentication in
  front of Glance if it is reachable from outside your network.
- The request is sent by the browser, not by the Glance server. The Home
  Assistant address has to work from the device you click on.
- If Glance is served over HTTPS, the webhook URL has to be HTTPS too.
  Browsers block plain-HTTP requests from HTTPS pages, and a page on a public
  domain may not call a private address at all. The row then says "Home
  Assistant unreachable".
- Only pending requests get buttons. A decided request stays on the list,
  faded, until the widget refreshes.

### Glance on a domain

If you open Glance through a Cloudflare tunnel or a reverse proxy, the buttons
have to reach Home Assistant the same way:

- Use Home Assistant's public HTTPS address in `ha-webhook-url`. If Home
  Assistant is not exposed yet, it is enough to route `/api/webhook/` to it; the
  rest of its UI can stay private.
- Turn "Local only" off in the blueprint. The request arrives through the
  tunnel, so Home Assistant does not count it as local.
- If Home Assistant has not been behind a proxy before, it also needs
  `use_x_forwarded_for: true` and the proxy's address under `trusted_proxies`
  in its `http:` config.

With "Local only" off, the webhook id is the only thing between the internet
and your request queue, so Glance itself must sit behind a login.

### "Sent", but nothing happens in Seerr

Home Assistant answers every webhook request with 200, whatever it does with it,
so the browser cannot tell these apart. Its log can (Settings → System → Logs,
search for `webhook`):

| Log line | Cause | Fix |
|---|---|---|
| `Received remote request for local webhook ...` | "Local only" is on, and the request came from outside | Turn "Local only" off, see above |
| `Received message for unregistered webhook ...` | The id in `ha-webhook-url` does not match the blueprint | Copy the id from the automation |
| `A request from a reverse proxy was received from ...` | Home Assistant does not trust the proxy | Add `use_x_forwarded_for` and `trusted_proxies` |

None of these? Open the automation's traces. A run that reached Seerr and
failed is also reported as a Home Assistant notification.

## Notes

- Posters come from `image.tmdb.org` and load in the browser.
- Status labels follow Seerr's own: Pending, Approved, Processing, Partial,
  Available, Declined, Failed.
- If Seerr cannot be reached, the widget shows the HTTP status and which
  variable to check instead of an empty list.
