import React, { useState, useEffect, KeyboardEvent } from "react";
import { API } from "aws-amplify";
import { Conversation } from "../common/types";
import ChatMessages from "../components/ChatMessages";
import LoadingGrid from "../../public/loading-grid.svg";

const Document: React.FC = () => {

  // Initialize an empty conversation
  const initialConversation: Conversation = {
    messages: [{
      type: "ai",
      content: "Hello! How can I help you today?",
    }]
  };

  const [conversation, setConversation] = useState<Conversation | null>(initialConversation);
  const [loading, setLoading] = React.useState<string>("idle");
  const [messageStatus, setMessageStatus] = useState<string>("idle");
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    // do nothing
  }, []);

  const handlePromptChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(event.target.value);
  };

  const handleKeyPress = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key == "Enter") {
      submitMessage();
    }
  };

  const submitMessage = async () => {
    setMessageStatus("loading");

    const previewMessage = {
      type: "text",
      content: prompt,
    };
    
    const updatedConversation = conversation
      ? { ...conversation, messages: [...conversation.messages, previewMessage] }
      : { messages: [previewMessage] };

    setConversation(updatedConversation);
    setPrompt("");

    // TODO: Implement API call to search Opensearch
    // const response = await API.post(
    //   "Api",
    //   `/${conversation?.document.documentid}/${conversation?.conversationid}`,
    //   {
    //     body: {
    //       prompt: prompt,
    //     },
    //   }
    // );
    
    const response = {
      type: "ai",
      content: "Some answers here",
    }

    const responsedConversation = {
      ...updatedConversation,
      messages: [...updatedConversation.messages, response],
    };

    setConversation(responsedConversation);
    setMessageStatus("idle");
  };

  return (
    <div className="">
      {loading === "loading" && !conversation && (
        <div className="flex flex-col items-center mt-6">
          <img src={LoadingGrid} width={40} />
        </div>
      )}
      {conversation && (
        <div className="grid border border-gray-200 rounded-lg">
          <ChatMessages
            prompt={prompt}
            conversation={conversation}
            messageStatus={messageStatus}
            submitMessage={submitMessage}
            handleKeyPress={handleKeyPress}
            handlePromptChange={handlePromptChange}
          />
        </div>
      )}
    </div>
  );
};

export default Document;
