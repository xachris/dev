// REACT 代码笔记
// 主题: useContext 组件间传递属性
// 日期: 20220223


// PART 1 导入钩子
import { useState, createContext, useContext } from "react";
import ReactDOM from "react-dom";


// 创建语境
const UserContext = createContext();


// PART 2 定义组件
function Component1() {

  // 设 user 初始状态为 某人名
  const [user, setUser] = useState("Jesse Hall");

  // 组件1渲染页面结果为 `Hello 某人名`
  return (
    <UserContext.Provider value={user}>
      <h1>{`Hello ${user}!`}</h1>
      <Component2 user={user} />

      {/* 测试此处若无 user={user} 也可正常显示 */}
      {/* <Component2 /> */}
    </UserContext.Provider>
  );
}

function Component2() {
  // 组件2渲染页面结果为 `Component 2`
  return (
    <>
      <h1>Component 2</h1>
      <Component3 />
    </>
  );
}

function Component3() {
  // 组件3渲染页面结果为 `Component 3`
  return (
    <>
      <h1>Component 3</h1>
      <Component4 />
    </>
  );
}

function Component4() {
  // 组件4渲染页面结果为 `Component 4`
  return (
    <>
      <h1>Component 4</h1>
      <Component5 />
    </>
  );
}

function Component5() {
  // 设置 user初始值 为全局语境的属性 value={user}
  const user = useContext(UserContext);

  // 组件5渲染页面结果为 `Component 5 ` + `Hello 某人名 again!`
  return (
    <>
      <h1>Component 5</h1>
      <h2>{`Hello ${user} again!`}</h2>
    </>
  );
}


// PART 3 渲染页面
ReactDOM.render(<Component1 />, document.getElementById("root"));