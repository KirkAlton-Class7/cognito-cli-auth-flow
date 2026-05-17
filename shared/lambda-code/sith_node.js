exports.handler = async (event) => {
    console.log("Incoming event:", JSON.stringify(event));

    const params = event.queryStringParameters || {};
    const name = params.name || "Chewbacca";

    const response = {
        message: `WELCOME ${name.toUpperCase()}. THE NODE SITH ROUTE HAS FELT YOUR PRESENCE.`,
        runtime: "node-sith",
        side: "sith",
    };

    console.log("Response:", JSON.stringify(response));

    return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(response),
    };
};
