import { useState, useEffect } from "react";
import { API } from "aws-amplify";
import { Attribute } from "../common/types";

const InitialAttributes: Attribute = {
  attributes: [
    {
      name: "custom:access_level",
      value: "nothon",
    },
    {
      name: "custom:department",
      value: "nothing",
    },
  ],
};

const Attributes: React.FC = () => {
  const [attributes, setAttributes] = useState<Attribute>(InitialAttributes);
  const [inputValues, setInputValues] = useState<{ [key: string]: string }>({});
  const [attributeStatus, setAttributeStatus] = useState<string>("idle");

  const fetchData = async () => {
    setAttributeStatus("loading");

    // TODO : Call API to get attributes
    // const attributes = await API.get("RestApi", "/attribute/", {});
    const attributes: Attribute = {
      attributes: [
        {
          name: "custom:access_level",
          value: "restricted",
        },
        {
          name: "custom:department",
          value: "engineering",
        },
      ],
    };

    setAttributeStatus("idle");
    setAttributes(attributes);

    // Initialize inputValues with the fetched data
    const initialValues: { [key: string]: string } = {};
    attributes.attributes.forEach((attr) => {
      initialValues[attr.name] = attr.value;
    });
    setInputValues(initialValues);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleInputChange = (name: string, value: string) => {
    setInputValues((prevValues) => ({
      ...prevValues,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // TODO: Call API to save attributes
    // const attributes = await API.post("RestApi", "/attribute/", {});
    console.log("Form submitted with values:", inputValues);
    // inputValues 
    // {
    //    "custom:access_level" : "restricted",
    //    "custom:department" : "engineering"
    // }
    setAttributeStatus("Successful");

  };

  return (
    <div className="justify-between pt-6 pb-4">
      {
        attributeStatus == "Successful" && (
          <div class="bg-teal-100 border-t-4 border-teal-500 rounded-b text-teal-900 px-4 py-3 shadow-md" role="alert">
            <div class="flex">
              <div class="py-1"><svg class="fill-current h-6 w-6 text-teal-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM9 11V9h2v6H9v-4zm0-6h2v2H9V5z"/></svg></div>
              <div>
                <p class="font-bold">Attributes updated successfully.</p>
              </div>
            </div>
          </div>
        )
      }
      <div className="w-full border-b-2 border-gray-300 pb-4">
        <h2 className="text-2xl font-bold">Manage my attributes</h2>
      </div>
      <div className="w-full">
        <form
          className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4"
          onSubmit={handleSubmit}
        >
          {attributes &&
            attributes.attributes.map((attribute, i) => (
              <div className="mb-4" key={i}>
                <label
                  className="block text-gray-700 text-sm font-bold mb-2"
                  htmlFor={attribute.name}
                >
                  {attribute.name}
                </label>
                <input
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  id={attribute.name}
                  type="text"
                  value={inputValues[attribute.name] || ""}
                  onChange={(e) =>
                    handleInputChange(attribute.name, e.target.value)
                  }
                />
              </div>
            ))}
          <div className="flex items-center justify-between">
            <button
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              type="submit"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Attributes;