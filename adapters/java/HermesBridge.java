import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * HERMES purpose-contract adapter for Syntra, IXO, APC/Odin or any Java tool.
 * Requires JDK 17+. Uses ONLY java.net.http and the hermes.purpose.v1 JSON API.
 * Does not read local files, execute remote jobs, or touch the Discord API.
 */
public final class HermesBridge {
    private final HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5)).followRedirects(HttpClient.Redirect.NEVER).build();
    private final URI base;
    private final String token;

    public HermesBridge(String url, String token) {
        this.base = URI.create(url.endsWith("/") ? url.substring(0, url.length()-1) : url);
        this.token = token;
        String host = base.getHost();
        if (host == null || base.getUserInfo() != null || base.getQuery() != null
                || base.getFragment() != null || (!base.getPath().isEmpty() && !base.getPath().equals("/"))) {
            throw new IllegalArgumentException("Invalid hub URL");
        }
        if (!base.getScheme().equals("https") && !(base.getScheme().equals("http")
                && (host.equals("127.0.0.1") || host.equals("localhost") || host.startsWith("10.")
                || host.startsWith("192.168.") || host.startsWith("100.")))) {
            throw new IllegalArgumentException("Use HTTPS or trusted private hub HTTP");
        }
        if (token == null || token.isBlank()) throw new IllegalArgumentException("HERMES_HUB_TOKEN is required");
    }

    /** Official API string, deliberately returned raw for language-neutral interoperability. */
    public String send(String path, String method, String jsonBody) throws IOException, InterruptedException {
        HttpRequest.Builder request = HttpRequest.newBuilder(base.resolve(path))
            .timeout(Duration.ofSeconds(20)).header("Authorization", "Bearer " + token)
            .header("Accept", "application/json");
        if (jsonBody == null) request.GET();
        else request.header("Content-Type", "application/json; charset=utf-8")
                    .method(method, HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8));
        HttpResponse<String> response = client.send(request.build(), HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() / 100 != 2) {
            throw new IOException("Hub HTTP " + response.statusCode() + ": " + response.body());
        }
        return response.body();
    }

    public String purposes() throws IOException, InterruptedException {
        return send("/api/v1/purposes", "GET", null);
    }

    public String preview(String name, String description, String project) throws IOException, InterruptedException {
        return send("/api/v1/route/preview", "POST", object(Map.of(
            "name",name, "description",description, "project",project)));
    }

    public String newPurpose(String slug, String title, String reason, String keywords)
            throws IOException, InterruptedException {
        List<String> terms = new ArrayList<>();
        for (String word : keywords.split(",")) if (!word.isBlank()) terms.add(word.trim());
        StringBuilder list = new StringBuilder("[");
        for (String term : terms) {
            if (list.length() > 1) list.append(',');
            list.append(q(term));
        }
        list.append(']');
        String body = object(Map.of("kind","new_purpose","proposed_slug",slug,
            "title",title,"reason",reason));
        body = body.substring(0,body.length()-1) + ",\"keywords\":" + list + "}";
        return send("/api/v1/purpose-requests", "POST", body);
    }

    public String missingFile(String title, String reason) throws IOException, InterruptedException {
        return send("/api/v1/purpose-requests", "POST", object(Map.of(
            "kind","missing_file", "title",title, "reason",reason)));
    }

    /** Compact JSON string scalar: escape control characters rather than assembling invalid JSON. */
    static String q(String input) {
        StringBuilder output = new StringBuilder("\"");
        for (int i=0;i<input.length();i++) {
            char c = input.charAt(i);
            switch(c) {
                case '"': output.append("\\\""); break;
                case '\\': output.append("\\\\"); break;
                case '\n': output.append("\\n"); break;
                case '\r': output.append("\\r"); break;
                case '\t': output.append("\\t"); break;
                default:
                    if (c < 32) output.append(String.format("\\u%04x",(int)c));
                    else output.append(c);
            }
        }
        return output.append('"').toString();
    }

    static String object(Map<String,String> values) {
        StringBuilder s = new StringBuilder("{");
        for (Map.Entry<String,String> e:values.entrySet()) {
            if (s.length() > 1) s.append(',');
            s.append(q(e.getKey())).append(':').append(q(e.getValue()));
        }
        return s.append('}').toString();
    }

    public static void main(String[] args) {
        if (args.length==1 && args[0].equals("selftest")) {
            if (!q("one\n\"two\"").equals("\"one\\n\\\"two\\\"\""))
                throw new IllegalStateException("JSON escaping failed");
            System.out.println("Java adapter JSON selftest: PASS");
            return;
        }
        try {
            HermesBridge hub = new HermesBridge(System.getenv().getOrDefault("HERMES_HUB_URL","http://127.0.0.1:8787"),
                System.getenv("HERMES_HUB_TOKEN"));
            String result;
            if (args.length==1 && args[0].equals("purposes")) result=hub.purposes();
            else if (args.length>=3 && args[0].equals("preview"))
                result=hub.preview(args[1],args[2],args.length>3?args[3]:"shared");
            else if (args.length==5 && args[0].equals("new-purpose"))
                result=hub.newPurpose(args[1],args[2],args[3],args[4]);
            else if (args.length==3 && args[0].equals("missing-file"))
                result=hub.missingFile(args[1],args[2]);
            else throw new IllegalArgumentException("Usage: purposes | preview NAME DESCRIPTION [PROJECT] | new-purpose SLUG TITLE REASON KEYWORDS | missing-file TITLE REASON");
            System.out.println(result);
        } catch (Exception error) {
            System.err.println("HERMES Java bridge: " + error.getMessage());
            System.exit(2);
        }
    }
}
