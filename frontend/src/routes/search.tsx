import React, { useState, useEffect, KeyboardEvent } from "react";
import { API } from "aws-amplify";
import SearchDocuments from "../components/SearchDocuments";

const Search: React.FC = () => {

  const [searchResult, setSearchResult] = useState<string | null>("");
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

    const response = await API.post(
      "RestApi",
      `/invoke`,
      {
        body: {
          prompt: prompt,
        },
      }
    );

    setSearchResult(response.content);
    setMessageStatus("idle");
  };

  return (
    <div className="">
        <div className="grid border border-gray-200 rounded-lg">
          <SearchDocuments
            prompt={prompt}
            searchResults={searchResult}
            messageStatus={messageStatus}
            submitMessage={submitMessage}
            handleKeyPress={handleKeyPress}
            handlePromptChange={handlePromptChange}
          />
        </div>
    </div>
  );
};

export default Search;
