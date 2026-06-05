const { DynamoDBClient, UpdateItemCommand } = require("@aws-sdk/client-dynamodb");

// CONFIGURATION
const client = new DynamoDBClient({});
const TOKEN_TABLE_NAME = process.env.TOKEN_TABLE_NAME || "jedi-token-holocron";

// HEADER LOOKUP
function getHeader(event, name) {
    const headers = event.headers || {};
    const wanted = name.toLowerCase();

    for (const [key, value] of Object.entries(headers)) {
        if (key.toLowerCase() === wanted) {
            return value;
        }
    }

    return null;
}

// DYNAMODB TOKEN UPDATE
async function markTokenUsed(tokenId, route) {
    const usedAt = new Date().toISOString();

    await client.send(
        new UpdateItemCommand({
            TableName: TOKEN_TABLE_NAME,
            Key: {
                token_id: { S: tokenId },
            },
            UpdateExpression: "SET used = :used, used_at = :used_at, used_route = :route",
            ExpressionAttributeValues: {
                ":used": { BOOL: true },
                ":used_at": { S: usedAt },
                ":route": { S: route },
            },
        })
    );

    return usedAt;
}

// LAMBDA HANDLER
exports.handler = async (event) => {
    console.log("Incoming event:", JSON.stringify(event));

    // Query string keeps the original Sith route greeting behavior.
    const params = event.queryStringParameters || {};
    const name = params.name || "Chewbacca";

    // x-token-id links this route invocation back to the helper-created record.
    const tokenId = getHeader(event, "x-token-id");
    const tokenTracking = {
        table: TOKEN_TABLE_NAME,
        token_id: tokenId,
        status: "missing-token-id",
    };

    if (tokenId) {
        try {
            const usedAt = await markTokenUsed(tokenId, "sith");
            tokenTracking.status = "marked-used";
            tokenTracking.used_at = usedAt;
        } catch (error) {
            console.log("Token tracking update failed:", error);
            tokenTracking.status = "update-failed";
            tokenTracking.error = String(error);
        }
    }

    // Return the original route response plus token tracking telemetry.
    const response = {
        message: `WELCOME ${name.toUpperCase()}. THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`,
        runtime: "node-sith",
        side: "sith",
        token_tracking: tokenTracking,
    };

    console.log("Response:", JSON.stringify(response));

    return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(response),
    };
};
