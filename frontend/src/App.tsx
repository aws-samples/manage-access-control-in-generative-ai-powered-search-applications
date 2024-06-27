import { Amplify, Auth } from "aws-amplify";
import { withAuthenticator } from "@aws-amplify/ui-react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";
import Layout from "./routes/layout";
import Search from "./routes/search";
import Attribute from "./routes/attribute"

Amplify.configure({
  Auth: {
    userPoolId: import.meta.env.VITE_USER_POOL_ID,
    userPoolWebClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID,
    region: import.meta.env.VITE_REGION,
  },
  API: {
    endpoints: [
      {
        name: "RestApi",
        endpoint: import.meta.env.VITE_API_ENDPOINT,
        region: import.meta.env.VITE_REGION,
        custom_header: async () => {
          return {
            Authorization: `Bearer ${(await Auth.currentSession())
              .getIdToken()
              .getJwtToken()}`,
            'x-access-token': `${(await Auth.currentSession())
              .getAccessToken()
              .getJwtToken()}`,
          };
        },
      }
    ],
  },
});

let router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        path: "/",
        Component: Search,
      },
      {
        path: "/attribute",
        Component: Attribute,
      },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default withAuthenticator(App, { hideSignUp: true });
