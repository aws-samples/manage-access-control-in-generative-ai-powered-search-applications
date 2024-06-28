import { useState, useEffect } from "react";
import { API } from "aws-amplify";
import { UnicornUser, CognitoUser, RequestStatus } from "../common/types";
import { convertCognitoToUnicorn, convertUnicornToCognito, departmentList, accessLevelList } from "../common/utilities"


const Attributes: React.FC = () => {
  const [users, setUsers] = useState<UnicornUser[]>([]);
  const [editUnicornUser, setEditUnicornUser] = useState<UnicornUser | null >();
  const [attributeStatus, setAttributeStatus] = useState<RequestStatus>({ status : "idle", message : "" });

  const fetchAttributes = async () => {
    setAttributeStatus({ status : "idle", message : "Loading" });

    try {
      const response = await API.get("RestApi", "/access", {});
      
      // Parse users
      const unicornUsers = response.users.map((user: CognitoUser) => {
        return convertCognitoToUnicorn(user)
      })
      
      setUsers(unicornUsers)
      setAttributeStatus({ status : "idle", message : "" });

    } catch (error: any) {
        // Handle the error as needed
        if (error.response) {
          setAttributeStatus({status: "error", message: "Ouch.... seems there is an issue. Tell your administrator this message : " + error.message})
        }
    }
  };

  const handleEditClick = async (i: number) => {
    setAttributeStatus({ status : "idle", message : "" })
    setEditUnicornUser(users[i])
    // console.log(users[i])
  }

  const handleSaveClick = async (i: number) => {

    setAttributeStatus({ status : "idle", message : "" })
    if (!editUnicornUser) return; // Ensure user is defined

    const cognitoUser = convertUnicornToCognito(editUnicornUser)

    const customAttributeList = cognitoUser.attributes.filter(attribute => attribute.Name.includes("custom:"))

    const cleanCognitoUser: CognitoUser = {
      username: cognitoUser!.username,
      attributes: customAttributeList
    }
    
    try {
      const response = await API.post("RestApi", "/access", {
        body: cleanCognitoUser,
      });

      setAttributeStatus({status: "successful", message: response})

      const updatedUsers = [
        ...users.slice(0, i),
        editUnicornUser,
        ...users.slice(i + 1)
      ];
      
      setUsers(updatedUsers)
      setEditUnicornUser(null)

    } catch (error: any) {
      // Handle the error as needed
      if (error.response) {
        setAttributeStatus({status: "error", message: "Ouch.... seems there is an issue. Tell your administrator this message : " + error.message})
      }
    }

  }

  const onDepartmentClick = (department: string) => {
    setAttributeStatus({ status : "idle", message : "" })

    const attributeList = editUnicornUser!.attributes['custom:department'].split(',');

    if (attributeList.includes(department) && attributeList.length === 1) {
      setAttributeStatus({status: "error", message: "User must belong to at least one department."})
      return
    }

    const newAttributeList = attributeList.includes(department)
    ? attributeList.filter(text => text !== department)
      : [...attributeList, department];

    const newUser: UnicornUser = {
      username: editUnicornUser!.username,
      attributes: {
        ...editUnicornUser!.attributes,
        'custom:department': newAttributeList.join(','),
      },
    };

    setEditUnicornUser(newUser);
    // console.log(newUser);
  };

  const onAccessLevelClick = (acessLevel: string) => {
    setAttributeStatus({ status : "idle", message : "" })
    const accessLevelList = editUnicornUser!.attributes['custom:access_level'].split(',');

    if (accessLevelList.includes(acessLevel) && accessLevelList.length === 1) {
      setAttributeStatus({status: "error", message: "User must have at least one access level."})
      return
    }

    const newAccessLevelList = accessLevelList.includes(acessLevel)
      ? accessLevelList.filter(text => text !== acessLevel)
      : [...accessLevelList, acessLevel];

    const newUser: UnicornUser = {
      username: editUnicornUser!.username,
      attributes: {
        ...editUnicornUser!.attributes,
        'custom:access_level': newAccessLevelList.join(','),
      },
    };

    setEditUnicornUser(newUser);
    // console.log(newUser);
  };


  useEffect(() => {
    fetchAttributes()
  }, []);

  return (
    <div className="justify-between pt-6 pb-2">
      {
        attributeStatus.status !=="idle" && (
          <div className={attributeStatus.status === "successful"
            ? "bg-blue-100 border-t-4 border-blue-500 rounded-b text-blue-900 px-4 py-3 shadow-md" 
            : attributeStatus.status === "error"
            ? "bg-rose-100 border-t-4 border-rose-500 rounded-b text-rose-900 px-4 py-3 shadow-md" 
            : "bg-neutral-100 border-t-4 border-neutral-500 rounded-b text-neutral-900 px-4 py-3 shadow-md" 
          }
          role="alert">
            <div className="flex">
              <div className="py-1"><svg className={attributeStatus.status === "successful"
                  ? "fill-current h-6 w-6 text-blue-500 mr-4" 
                  : attributeStatus.status === "error"
                  ? "fill-current h-6 w-6 text-rose-500 mr-4"
                  : "fill-current h-6 w-6 text-neutral-500 mr-4"
                }
                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM9 11V9h2v6H9v-4zm0-6h2v2H9V5z"/></svg></div>
              <div>
                <p className="font-bold">{attributeStatus.message}</p>
              </div>
            </div>
          </div>
        )
      }
      <div className="w-full border-b-2 border-gray-300 pb-4 pt-2">
        <h2 className="text-2xl font-bold">Manage permission</h2>
      </div>

      <div className="relative overflow-x-auto shadow-md sm:rounded-lg">
          <table className="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                  <tr>
                      <th scope="col" className="px-6 py-3">
                          User Name
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Email
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Department
                      </th>
                      <th scope="col" className="px-6 py-3">
                          Access Level
                      </th>
                      <th scope="col" className="px-6 py-3">
                          <span className="sr-only">Edit</span>
                      </th>
                  </tr>
              </thead>
              <tbody>
                {
                  users.map((unicornUser, i) => (
                    <tr className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                        key={`${'row_'+i}`}
                    >
                        <th scope="row" className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                          {unicornUser.username}
                        </th>
                        <td className="px-6 py-4">
                          {unicornUser.attributes.email}
                        </td>
                        <td className="px-6 py-4">
                          {(!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)) && (
                            <button id={`${i+'departmentDropdownCheckboxButton'}`} className="text-white bg-fuchsia-700 hover:bg-fuchsia-800 focus:ring-4 focus:outline-none focus:ring-fuchsia-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:bg-fuchsia-600 dark:hover:bg-fuchsia-700 dark:focus:ring-fuchsia-800" type="button">
                              {unicornUser.attributes["custom:department"]}
                            </button>
                          )}
                          {editUnicornUser && editUnicornUser.attributes.sub === unicornUser.attributes.sub && (
                            <ul className="p-3 space-y-3 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="departmentDropdownCheckboxButton" key={`${i+'_department'}`}>
                            {departmentList.map((department) => (
                            <li key={`${i+'_'+department}`}>
                              <div className="flex items-center">
                                <input id={`${i+'_'+department}`} type="checkbox" value="" className="w-4 h-4 text-fuchsia-600 bg-gray-100 border-gray-300 rounded focus:ring-fuchsia-500 dark:focus:ring-fuchsia-600 dark:ring-offset-gray-700 dark:focus:ring-offset-gray-700 focus:ring-2 dark:bg-gray-600 dark:border-gray-500"
                                onChange={() => onDepartmentClick(department)}
                                checked={editUnicornUser.attributes['custom:department'].includes(department)}
                                />
                                <label htmlFor={`${i+'_'+department}`} className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300">{department}</label>
                              </div>
                            </li>
                            ))}
                          </ul>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {(!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)) && (
                            <button id={`${i+'accessLevelDropdownCheckboxButton'}`} className="text-white bg-fuchsia-700 hover:bg-fuchsia-800 focus:ring-4 focus:outline-none focus:ring-fuchsia-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:bg-fuchsia-600 dark:hover:bg-fuchsia-700 dark:focus:ring-fuchsia-800" type="button">
                              {unicornUser.attributes["custom:access_level"]}
                            </button>
                          )}
                          {editUnicornUser && editUnicornUser.attributes.sub === unicornUser.attributes.sub && (
                            <ul className="p-3 space-y-3 text-sm text-gray-700 dark:text-gray-200" aria-labelledby={`${i+'accessLevelDropdownCheckboxButton'}`} key={`${i+'_accessLevel'}`}>
                            {accessLevelList.map((accessLevel) => (
                            <li key={`${i+'_'+accessLevel}`}>
                              <div className="flex items-center">
                                <input id={`${i+'_'+accessLevel}`} type="checkbox" value="" className="w-4 h-4 text-fuchsia-600 bg-gray-100 border-gray-300 rounded focus:ring-fuchsia-500 dark:focus:ring-fuchsia-600 dark:ring-offset-gray-700 dark:focus:ring-offset-gray-700 focus:ring-2 dark:bg-gray-600 dark:border-gray-500"
                                onChange={() => onAccessLevelClick(accessLevel)}
                                checked={editUnicornUser.attributes['custom:access_level'].includes(accessLevel)}
                                />
                                <label htmlFor={`${i+'_'+accessLevel}`} className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300">{accessLevel}</label>
                              </div>
                            </li>
                            ))}
                          </ul>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                            {(!editUnicornUser || (editUnicornUser && editUnicornUser.attributes.sub !== unicornUser.attributes.sub)) && (
                              <button type="button" 
                                className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                                onClick={() => handleEditClick(i)}
                              >
                              Edit
                            </button> )
                            }

                            {editUnicornUser && editUnicornUser.attributes.sub === unicornUser.attributes.sub && (
                              <button type="button" 
                                className="text-white bg-fuchsia-700 hover:bg-fuchsia-800 focus:ring-4 focus:ring-fuchsia-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-fuchsia-600 dark:hover:bg-fuchsia-700 focus:outline-none dark:focus:ring-fuchsia-800"
                                onClick={() => handleSaveClick(i)}
                              >
                              Save
                            </button> )
                            }

                        </td>
                    </tr>
                  ))
                }
              </tbody>
          </table>
      </div>

    </div>
  );
};

export default Attributes;