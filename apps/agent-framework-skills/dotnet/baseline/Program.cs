// BASELINE — written from generic / pre-skill knowledge of Microsoft Agent Framework.
// Errors and wrong guesses are recorded in COMPARISON.md.
//
// Intentional "generic knowledge" choices (may be stale):
// - Construct ChatClientAgent directly with instructions + AIFunctionFactory tools
// - Hand-roll a fake IChatClient that emits FunctionCallContent then text
// - Assume Microsoft.Extensions.AI 9.x (corrected at restore time to 10.11.0)

using System.ComponentModel;
using System.Text.Json;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

string dataPath = FindDataFile();
var store = JdeJobStore.Load(dataPath);

IChatClient chatClient = new ScriptedOpsChatClient();

AIAgent agent = new ChatClientAgent(
    chatClient,
    instructions: """
        You are a JD Edwards ops helper. Use the provided tools to look up batch job
        status from the Work with Submitted Jobs (WSJ) mock data. Answer briefly.
        """,
    name: "jde-ops-helper-baseline",
    description: "Offline JDE batch-job status helper (baseline, pre-skill).",
    tools:
    [
        AIFunctionFactory.Create(store.GetJobStatus),
        AIFunctionFactory.Create(store.ListActiveJobs),
    ]);

Console.WriteLine("=== .NET baseline (without skill) ===");
Console.WriteLine($"Data: {dataPath}");
Console.WriteLine();

string prompt = "What is the status of job 570213? Include the report id and any error text.";
Console.WriteLine($"User: {prompt}");
Console.WriteLine();

AgentResponse response = await agent.RunAsync(prompt);

foreach (ChatMessage message in response.Messages)
{
    Console.WriteLine($"[{message.Role}]");
    foreach (AIContent content in message.Contents)
    {
        switch (content)
        {
            case FunctionCallContent call:
                Console.WriteLine($"  tool_call {call.Name}({JsonSerializer.Serialize(call.Arguments)})");
                break;
            case FunctionResultContent result:
                Console.WriteLine($"  tool_result {result.CallId}: {result.Result}");
                break;
            case TextContent text when !string.IsNullOrWhiteSpace(text.Text):
                Console.WriteLine($"  {text.Text}");
                break;
            default:
                Console.WriteLine($"  {content}");
                break;
        }
    }
}

Console.WriteLine();
Console.WriteLine($"Final: {response.Text}");

static string FindDataFile()
{
    string? dir = AppContext.BaseDirectory;
    for (int i = 0; i < 8 && dir is not null; i++)
    {
        string candidate = Path.Combine(dir, "data", "jde-jobs.json");
        if (File.Exists(candidate))
        {
            return Path.GetFullPath(candidate);
        }

        candidate = Path.Combine(dir, "..", "..", "..", "..", "..", "data", "jde-jobs.json");
        if (File.Exists(Path.GetFullPath(candidate)))
        {
            return Path.GetFullPath(candidate);
        }

        dir = Directory.GetParent(dir)?.FullName;
    }

    // Walk up from CWD as a fallback for `dotnet run`.
    dir = Directory.GetCurrentDirectory();
    for (int i = 0; i < 8 && dir is not null; i++)
    {
        string candidate = Path.Combine(dir, "data", "jde-jobs.json");
        if (File.Exists(candidate))
        {
            return Path.GetFullPath(candidate);
        }

        dir = Directory.GetParent(dir)?.FullName;
    }

    throw new FileNotFoundException("Could not locate data/jde-jobs.json");
}

sealed class JdeJobStore
{
    private readonly JsonElement _root;
    private readonly Dictionary<string, string> _statusCodes;

    private JdeJobStore(JsonElement root, Dictionary<string, string> statusCodes)
    {
        _root = root;
        _statusCodes = statusCodes;
    }

    public static JdeJobStore Load(string path)
    {
        using FileStream stream = File.OpenRead(path);
        using JsonDocument doc = JsonDocument.Parse(stream);
        JsonElement root = doc.RootElement.Clone();
        var codes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (JsonProperty prop in root.GetProperty("statusCodes").EnumerateObject())
        {
            codes[prop.Name] = prop.Value.GetString() ?? prop.Name;
        }

        return new JdeJobStore(root, codes);
    }

    [Description("Look up a JD Edwards submitted batch job by job number.")]
    public string GetJobStatus(
        [Description("The JDE job number, e.g. 570213")] long jobNumber)
    {
        foreach (JsonElement job in _root.GetProperty("jobs").EnumerateArray())
        {
            if (job.GetProperty("jobNumber").GetInt64() == jobNumber)
            {
                string code = job.GetProperty("status").GetString() ?? "?";
                string label = _statusCodes.GetValueOrDefault(code, code);
                string? error = job.TryGetProperty("errorText", out JsonElement err)
                    ? err.GetString()
                    : null;
                return JsonSerializer.Serialize(new
                {
                    jobNumber,
                    reportId = job.GetProperty("reportId").GetString(),
                    version = job.GetProperty("version").GetString(),
                    description = job.GetProperty("description").GetString(),
                    status = code,
                    statusLabel = label,
                    user = job.GetProperty("user").GetString(),
                    queue = job.GetProperty("queue").GetString(),
                    errorText = error,
                });
            }
        }

        return JsonSerializer.Serialize(new { error = $"Job {jobNumber} not found" });
    }

    [Description("List JD Edwards submitted jobs that are not yet Done.")]
    public string ListActiveJobs()
    {
        var active = new List<object>();
        foreach (JsonElement job in _root.GetProperty("jobs").EnumerateArray())
        {
            string code = job.GetProperty("status").GetString() ?? "?";
            if (code is "D")
            {
                continue;
            }

            active.Add(new
            {
                jobNumber = job.GetProperty("jobNumber").GetInt64(),
                reportId = job.GetProperty("reportId").GetString(),
                status = code,
                statusLabel = _statusCodes.GetValueOrDefault(code, code),
                description = job.GetProperty("description").GetString(),
            });
        }

        return JsonSerializer.Serialize(active);
    }
}

/// <summary>
/// Scripted offline chat client: first turn requests get_job_status(570213),
/// second turn returns a short natural-language answer. No network, no keys.
/// </summary>
sealed class ScriptedOpsChatClient : IChatClient
{
    private int _turn;

    public ChatClientMetadata Metadata { get; } = new("scripted-ops-baseline");

    public async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        _turn++;

        // After the agent posts a function result, emit the final answer.
        bool hasFunctionResult = messages.SelectMany(m => m.Contents).OfType<FunctionResultContent>().Any();
        if (hasFunctionResult || _turn > 1)
        {
            return new ChatResponse(
                new ChatMessage(ChatRole.Assistant,
                    "Job 570213 (R31410 / Work Order Processing) is in Error (E). " +
                    "errorText: Work order 451882 failed: branch/plant M30 record invalid (error 0002E)."));
        }

        return new ChatResponse(
            new ChatMessage(ChatRole.Assistant,
            [
                new FunctionCallContent(
                    callId: "call_baseline_1",
                    name: "GetJobStatus",
                    arguments: new Dictionary<string, object?> { ["jobNumber"] = 570213L }),
            ]));
    }

    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatResponse response = await GetResponseAsync(messages, options, cancellationToken);
        foreach (ChatMessage message in response.Messages)
        {
            yield return new ChatResponseUpdate(message.Role, message.Contents);
        }
    }

    public object? GetService(Type serviceType, object? serviceKey = null) =>
        serviceType.IsInstanceOfType(this) ? this : null;

    public void Dispose()
    {
    }
}
