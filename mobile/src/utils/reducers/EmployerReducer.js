const EmployerReducer = (state, action) => {
    switch (action.type) {
        case "SET_PROFILE":
            return action.payload; 
        case "UPDATE_PROFILE":
            return { ...state, ...action.payload };
        case "CLEAR_PROFILE":
            return null;
        default:
            return state;
    }
};

export default EmployerReducer;