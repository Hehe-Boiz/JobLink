import { View, Image } from 'react-native';
import { Dialog, Button, Portal } from 'react-native-paper';
import CustomText from './CustomText';
import styles from '../../styles/Job/JobDetailStyles'

const AppDialog = ({ visible, onDismiss, title, content, type = 'success', buttonText = 'ĐÓNG', onButtonPress }) => {

    const iconSource = type === 'success'
        ? { uri: 'https://cdn-icons-png.flaticon.com/512/148/148767.png' } 
        : { uri: 'https://cdn-icons-png.flaticon.com/512/190/190406.png' }; 

    const handlePress = () => {
        if (onButtonPress) onButtonPress();
        onDismiss();
    }
    return (
        <Portal>
            <Dialog
                visible={visible}
                onDismiss={onDismiss}
                style={styles.dialogContainer}
            >
                <View style={styles.dialogContentWrapper}>
                    <Image
                        source={iconSource}
                        style={styles.dialogIcon}
                    />

                    <CustomText style={styles.dialogTitle}>
                        {title}
                    </CustomText>

                    <Dialog.Content>
                        <CustomText style={styles.dialogText}>
                           {content}
                        </CustomText>
                    </Dialog.Content>

                    <Dialog.Actions style={styles.dialogActions}>
                        <Button
                            mode="contained"
                            onPress={handlePress}
                            style={styles.dialogButton}
                            labelStyle={styles.dialogButtonLabel}
                        >
                            {buttonText}
                        </Button>
                    </Dialog.Actions>
                </View>
            </Dialog>
        </Portal>
    )
}
export default AppDialog;