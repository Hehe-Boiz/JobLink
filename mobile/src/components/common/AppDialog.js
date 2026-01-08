import React from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { Dialog, Button, Portal } from 'react-native-paper';
import CustomText from '../CustomText'; 
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

const styles = StyleSheet.create({
    dialogContainer: {
        backgroundColor: 'white',
        borderRadius: 20,
        paddingBottom: 20,
        marginHorizontal: 30, // Căn lề cho popup đỡ bị sát viền
    },
    dialogContentWrapper: {
        alignItems: 'center',
        paddingTop: 20,
    },
    dialogIcon: {
        width: 60,
        height: 60,
        marginBottom: 15,
    },
    dialogTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 10,
    },
    dialogText: {
        fontSize: 14,
        color: '#524B6B',
        textAlign: 'center',
        lineHeight: 22,
    },
    dialogActions: {
        flexDirection: 'row', // Xếp ngang 2 nút
        justifyContent: 'space-between',
        width: '100%',
        paddingHorizontal: 20,
        marginTop: 10,
    },
    dialogButton: {
        borderRadius: 10,
        width: '100%', // Mặc định full nếu 1 nút
    },
    cancelButton: {
        flex: 1, 
        borderColor: '#EAEAEA',
        backgroundColor: 'white'
    },
    dialogButtonLabel: {
        fontSize: 14,
        fontWeight: 'bold',
        paddingVertical: 2,
    },
});

export default AppDialog;