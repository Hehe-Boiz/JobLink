import React, { createContext, useState, useContext } from 'react';
import AppDialog from '../../components/common/AppDialog';


const DialogContext = createContext();

export const DialogProvider = ({ children }) => {
    const [visible, setVisible] = useState(false);
    const [config, setConfig] = useState({
        title: '',
        content: '',
        type: 'success',
        buttonText: 'ĐÓNG',
        onPress: null,
    });

    const showDialog = ({ title, content, type = 'success', buttonText = 'ĐÓNG', onPress = null }) => {
        setConfig({ title, content, type, buttonText, onPress });
        setVisible(true);
    };

    const hideDialog = () => {
        setVisible(false);
    };

    return (
        <DialogContext.Provider value={{ showDialog, hideDialog }}>
            {children}
            <AppDialog
                visible={visible}
                onDismiss={hideDialog}
                title={config.title}
                content={config.content}
                type={config.type}
                buttonText={config.buttonText}
                onButtonPress={config.onPress}
            />
        </DialogContext.Provider>
    );
};

export default DialogContext;