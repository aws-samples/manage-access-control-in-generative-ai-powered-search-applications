import { Link } from "react-router-dom";
import { Menu } from "@headlessui/react";
import {
  ArrowLeftOnRectangleIcon,
  ChevronDownIcon,
  TagIcon,
} from "@heroicons/react/24/outline";
import UnicornLogo from '../../public/favicon.ico'
import { Auth } from 'aws-amplify';
import { useState, useEffect} from 'react';

interface NavigationProps {
  userInfo: any;
  handleSignOutClick: (
    event: React.MouseEvent<HTMLButtonElement>
  ) => Promise<void>;
}

const Navigation: React.FC<NavigationProps> = ({
  userInfo,
  handleSignOutClick,
}: NavigationProps) => {
  const [role, setRole] = useState<string | null>(null);

  const fetchAdmin = async () => {
    try {
      const { attributes } = await Auth.currentUserInfo();
      setRole(attributes['custom:role'])
    } catch (err) {
      console.log(err);
    }
  }

  useEffect(() => {
    fetchAdmin()
  }, []);

  return (
    <nav className="bg-fuchsia-400">
      <div className="container flex flex-wrap items-center justify-between py-3">
        <Link
          to="/"
          className="inline-flex items-center self-center text-2xl font-semibold whitespace-nowrap text-white"
        >
          <img src={UnicornLogo} className="w-6 h-6 mr-1.5" />
          Unicorn Robotics Factory
        </Link>
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
          {role === 'admin' && <div className="relative ml-3">
            <Link
                to="/attribute"
                className="group w-full inline-flex items-center rounded-md px-2 py-2 text-sm text-white underline-offset-2 hover:underline"
            >
              <TagIcon className="w-4 h-4 mr-1" />
              Manage Attributes
            </Link>
          </div>}
          <div className="relative ml-3">
            <Menu>
              <Menu.Button className="text-center inline-flex items-center text-white text-sm underline-offset-2 hover:underline">
                {userInfo?.username}
                <ChevronDownIcon className="w-3 h-3 ml-1 text-white" />
              </Menu.Button>
              <Menu.Items className="absolute right-0 z-10 mt-2 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                <div className="px-1 py-1 ">
                  <Menu.Item>
                    <button
                      onClick={handleSignOutClick}
                      className="group w-full inline-flex items-center rounded-md px-2 py-2 text-sm underline-offset-2 hover:underline"
                    >
                      <ArrowLeftOnRectangleIcon className="w-4 h-4 mr-1" />
                      Sign Out
                    </button>
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Menu>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
