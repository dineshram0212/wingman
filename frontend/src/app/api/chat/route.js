// app/api/messages/route.js
export async function POST(req) {
    const { message } = await req.json()
  
    try {
      const backendResponse = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_input: message }),
      })
  
      const data = await backendResponse.json()
  
      return Response.json({ response: data.response })
    } catch (error) {
      console.error('Error calling Python backend:', error)
      return new Response(JSON.stringify({ message: 'Internal server error' }), {
        status: 500,
      })
    }
  }
  