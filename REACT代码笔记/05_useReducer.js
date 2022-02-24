// REACT 代码笔记
// 主题: useReducer 待办事项
// 日期: 20220224

// 总结: useReducer 用于为状态设定逻辑, 传入一个 recuder函数, 一个状态对象, 返回一个状态对象, 一个dispatch函数

// PART 1 导入钩子
import { useReducer } from "react";
import ReactDOM from "react-dom";

// 设定初始状态对象
const initialTodos = [
  {
    id: 1,                  // ID为 1
    title: "Todo 1",        // 待办事项 1
    complete: false,        // 默认未完成
  },
  {
    id: 2,                  // ID为 2
    title: "Todo 2",        // 待办事项 2
    complete: false,        // 默认未完成
  },
];


// 设定归约逻辑
const reducer = (state, action) => {                    // 传入默认的 状态对象 动作对象
  switch (action.type) {                                // 传入 动作对象之类型
    case "COMPLETE":                                    // 若 动作对象 为 完成
      return state.map((todo) => {                      // 则 返回 状态的映射:
        if (todo.id === action.id) {                    // 对于每个对象内容, 若状态ID等于动作ID
          return { ...todo, complete: !todo.complete }; // 则反转完成状态的 true / false 值
        } else {                                        // 否则
          return todo;                                  // 维持状态不变
        }
      });
    default:
      return state;                                     // 默认状态不变
  }
};


// PART 2 定义组件
function Todos() {

  // 使用 useReducer() 设定 初始状态 和 处置函数
  const [todos, dispatch] = useReducer(reducer, initialTodos);

  const handleComplete = (todo) => {                  // 发起处置函数
    dispatch({ type: "COMPLETE", id: todo.id });      // 调用归约逻辑, 传入action对象
  };

  return (
    <>
      {todos.map((todo) => (                          // 映射每一个对象内容, 各成一行
        <div key={todo.id}>                           
          <label>
            <input                                    // 输入框
              type="checkbox"                         // 类型为勾选(单选)
              checked={todo.complete}                 // 初始状态为当前代办事项的 compete属性
              onChange={() => handleComplete(todo)}   // 事件监听: 若勾选状态变化, 则调用处置函数
            />
            {todo.title}
          </label>
        </div>
      ))}
    </>
  );
}


// PART 3 渲染页面
ReactDOM.render(<Todos />, document.getElementById("root"));