// WITH-SKILL — written after reading vendor/skills/agent-framework-builder-dotnet.
// Path chosen: plain agent (agent-builder.md). Not harness / workflow.
//
// Skill-guided choices applied here:
// - Smallest pattern: one ChatClientAgent + tools + sessions would be enough
// - Prefer chatClient.AsAIAgent(...) (stable pattern from agent-builder.md)
// - Tools via AIFunctionFactory.Create + [Description] on static methods (official sample style)
// - Fake IChatClient for deterministic offline validation (skill Validation §3)
// - Env-driven provider switch documented in .env.example (no secrets; framework does not
//   read configuration on your behalf — we pass values explicitly)
// - Narrow packages: Microsoft.Agents.AI (+ Microsoft.Extensions.AI)

using System.ComponentModel;
using System.Text.Json;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

string dataPath = FindDataFile();
JdeJobStore.Load(dataPath);

IChatClient chatClient = CreateChatClient();

AIAgent agent = chatClient.AsAIAgent(
    instructions: """
        You are a JD Edwards ops helper. Use the provided tools to look up batch job
        status from the Work with Submitted Jobs (WSJ) mock data. Answer briefly.
        """,
    name: "jde-ops-helper",
    description: "Offline JDE batch-job status helper (skill-guided).",
    tools:
    [
        AIFunctionFactory.Create(JdeJobStore.GetJobStatus),
        AIFunctionFactory.Create(JdeJobStore.ListActiveJobs),
    ]);

Console.WriteLine("=== .NET with-skill (agent-framework-builder-dotnet) ===");
Console.WriteLine($"Data: {dataPath}");
Console.WriteLine($"Chat client: {chatClient.GetService(typeof(ChatClientMetadata))}");
Console.WriteLine();

string prompt = "What is the status of job 570213? Include the report id and any error text.";
Console.WriteLine($"User: {prompt}");
Console.WriteLine();

// Skill: create a session when the conversation is multi-turn; single-shot still works
// without one, but creating it matches the documented session pattern.
AgentSession session = await agent.CreateSessionAsync();
AgentResponse response = await agent.RunAsync(prompt, session);

PrintResponse(response);
Console.WriteLine();
Console.WriteLine($"Final: {response.Text}");

static IChatClient CreateChatClient()
{
    // Skill: Agent Framework does not read configuration for you — pass provider
    // settings explicitly. Default is the scripted offline client (no keys).
    string mode = Environment.GetEnvironmentVariable("AF_CHAT_MODE") ?? "scripted";
    if (string.Equals(mode, "openai", StringComparison.OrdinalIgnoreCase))
    {
        throw new InvalidOperationException(
            "Live OpenAI mode is documented in .env.example. Add Microsoft.Agents.AI.OpenAI " +
            "and wire OpenAIResponseClient/ChatClient.AsAIAgent per the skill's provider table. " +
            "This demo's default path stays scripted so CI needs no keys.");
    }

    return new ScriptedOpsChatClient();
}

static void PrintResponse(AgentResponse response)
{
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
}

static string FindDataFile()
{
    string? dir = AppContext.BaseDirectory;
    for (int i = 0; i < 8 && dir is not null; i++)
    {
        string candidate = Path.GetFullPath(Path.Combine(dir, "data", "jde-jobs.json"));
        if (File.Exists(candidate))
        {
            return candidate;
        }

        candidate = Path.GetFullPath(Path.Combine(dir, "..", "..", "..", "..", "..", "data", "jde-jobs.json"));
        if (File.Exists(candidate))
        {
            return candidate;
        }

        dir = Directory.GetParent(dir)?.FullName;
    }

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

/// <summary>Static tool surface matching the skill's preferred AIFunctionFactory.Create style.</summary>
static class JdeJobStore
{
    private static JsonElement _root;
    private static Dictionary<string, string> _statusCodes = new(StringComparer.OrdinalIgnoreCase);

    public static void Load(string path)
    {
        using FileStream stream = File.OpenRead(path);
        using JsonDocument doc = JsonDocument.Parse(stream);
        _root = doc.RootElement.Clone();
        _statusCodes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (JsonProperty prop in _root.GetProperty("statusCodes").EnumerateObject())
        {
            _statusCodes[prop.Name] = prop.Value.GetString() ?? prop.Name;
        }
    }

    [Description("Look up a JD Edwards submitted batch job by job number.")]
    public static string GetJobStatus(
        [Description("The JDE job number, e.g. 570213")] long jobNumber)
    {
        foreach (JsonElement job in _root.GetProperty("jobs").EnumerateArray())
        {
            if (job.GetProperty("jobNumber").GetInt64() == jobNumber)
            {
                string code = job.GetProperty("status").GetString() ?? "?";
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
                    statusLabel = _statusCodes.GetValueOrDefault(code, code),
                    user = job.GetProperty("user").GetString(),
                    queue = job.GetProperty("queue").GetString(),
                    errorText = error,
                });
            }
        }

        return JsonSerializer.Serialize(new { error = $"Job {jobNumber} not found" });
    }

    [Description("List JD Edwards submitted jobs that are not yet Done.")]
    public static string ListActiveJobs()
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
/// Scripted offline IChatClient (skill Extensibility + Validation): first turn emits a
/// FunctionCallContent; after the function-invocation layer posts the tool result, return text.
/// ChatClientAgent wraps this client with function invocation unless UseProvidedChatClientAsIs.
/// </summary>
sealed class ScriptedOpsChatClient : IChatClient
{
    private int _turn;

    public async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        _turn++;

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
                    callId: "call_skill_1",
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

    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        if (serviceType == typeof(ChatClientMetadata))
        {
            return new ChatClientMetadata("scripted-ops-with-skill");
        }

        return serviceType.IsInstanceOfType(this) ? this : null;
    }

    public void Dispose()
    {
    }
}
