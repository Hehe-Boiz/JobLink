import React, { createContext, useState, useContext } from 'react';
import AppDialog from '../../components/common/AppDialog';

const DialogContext = createContext();

export const DialogProvider = ({ children }) => {
    const [visible, setVisible] = useState(false);

    const [config, setConfig] = useState({
        title: '',
        content: '',
        type: 'success',
        confirmText: 'ĐÓNG',
        cancelText: 'HỦY',
        onConfirm: null,
        onCancel: null,
        showCancel: false,
    });

    /**
     * @param {Object} options 
     * options = { title, content, type, onConfirm, onCancel, showCancel, confirmText, cancelText }
     */
    const showDialog = (options) => {
        setConfig({
            title: options.title || 'Thông báo',
            content: options.content || '',
            type: options.type || 'success',

            confirmText: options.confirmText || (options.showCancel ? 'XÁC NHẬN' : 'ĐÓNG'),
            cancelText: options.cancelText || 'HỦY',

            onConfirm: options.onConfirm || null,
            onCancel: options.onCancel || null,

            showCancel: options.showCancel || false,
        });
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
                {...config}
            />
        </DialogContext.Provider>
    );
};

export default DialogContext;