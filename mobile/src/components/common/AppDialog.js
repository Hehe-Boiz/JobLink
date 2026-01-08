import React from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { Dialog, Button, Portal } from 'react-native-paper';
import CustomText from '../../components/common/CustomText' ; 
import styles from '../../styles/Job/JobDetailStyles'

const AppDialog = ({ 
    visible, 
    onDismiss, 
    title, 
    content, 
    type = 'success', 
    confirmText = 'ĐÓNG', 
    cancelText = 'HỦY',
    onConfirm,
    onCancel,
    showCancel = false // Cờ để bật chế độ Confirm
}) => {

    // 1. Cấu hình Icon và Màu sắc động theo Type
    const config = {
        success: {
            icon: 'https://cdn-icons-png.flaticon.com/512/148/148767.png', // Tích xanh
            color: '#130160', // Màu chủ đạo
        },
        error: {
            icon: 'https://cdn-icons-png.flaticon.com/512/190/190406.png', // Dấu X đỏ
            color: '#FF4D4D',
        },
        warning: {
            icon: 'https://cdn-icons-png.flaticon.com/512/1008/1008948.png', // Dấu than vàng
            color: '#FF9228', // Màu cam cảnh báo
        }
    };

    const currentConfig = config[type] || config.success;

    const handleConfirm = () => {
        if (onConfirm) onConfirm();
        onDismiss();
    };

    const handleCancel = () => {
        if (onCancel) onCancel();
        onDismiss();
    };

    return (
        <Portal>
            <Dialog
                visible={visible}
                onDismiss={onDismiss}
                style={styles.dialogContainer}
            >
                <View style={styles.dialogContentWrapper}>
                    <Image
                        source={{ uri: currentConfig.icon }}
                        style={styles.dialogIcon}
                        resizeMode="contain"
                    />

                    <CustomText style={[styles.dialogTitle, { color: currentConfig.color }]}>
                        {title}
                    </CustomText>

                    <Dialog.Content>
                        <CustomText style={styles.dialogText}>
                           {content}
                        </CustomText>
                    </Dialog.Content>

                    <Dialog.Actions style={styles.dialogActions}>
                        {/* Nút Hủy (Chỉ hiện khi showCancel = true) */}
                        {showCancel && (
                            <Button
                                mode="outlined"
                                onPress={handleCancel}
                                style={[styles.dialogButton, styles.cancelButton]}
                                labelStyle={[styles.dialogButtonLabel, { color: '#524B6B' }]}
                                theme={{ colors: { outline: '#EAEAEA' } }}
                            >
                                {cancelText}
                            </Button>
                        )}

                        {/* Nút Xác nhận */}
                        <Button
                            mode="contained"
                            onPress={handleConfirm}
                            style={[
                                styles.dialogButton, 
                                { backgroundColor: currentConfig.color, flex: 1, marginLeft: showCancel ? 10 : 0 }
                            ]}
                            labelStyle={styles.dialogButtonLabel}
                        >
                            {confirmText}
                        </Button>
                    </Dialog.Actions>
                </View>
            </Dialog>
        </Portal>
    )
}


export default AppDialog;